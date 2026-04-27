import json
import asyncio
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

from core.orchestrator import Orchestrator

app = FastAPI(
    title="AMR Navigation Agent API",
    description="Scalable streaming API for AMR navigation mission planning.",
    version="2.0.0"
)

# Enable CORS for React/Frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared orchestrator instance
orchestrator = Orchestrator()

class QueryRequest(BaseModel):
    query: str

@app.get("/health")
async def health_check():
    return {"status": "online", "system": "AMR Navigation Agent"}

@app.post("/api/query")
async def handle_query(request: QueryRequest):
    """Simple POST endpoint for one-shot mission planning."""
    result = await orchestrator.handle(request.query)
    try:
        return {"result": json.loads(result)}
    except (json.JSONDecodeError, TypeError):
        return {"result": result}

@app.post("/api/stream")
async def stream_query(request: QueryRequest):
    """
    Streaming endpoint using Server-Sent Events (SSE).
    Perfect for real-time progress updates on the client side.
    """
    async def event_generator():
        async for event in orchestrator.handle_streaming(request.query):
            # Convert ProgressEvent to a JSON string for SSE
            yield f"data: {json.dumps(event.to_dict())}\n\n"
            await asyncio.sleep(0.01) # Yield control

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

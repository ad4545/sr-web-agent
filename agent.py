from typing import TypedDict
from langgraph.graph import StateGraph, START, END
import asyncio
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

from core.orchestrator import Orchestrator

# Initialize the orchestrator
orchestrator = Orchestrator()

class AgentState(TypedDict):
    input: str
    output: str

async def run_orchestrator(state: AgentState):
    """
    This node wraps the existing Orchestrator logic.
    It takes the 'input' from the state, processes it, and returns the 'output'.
    """
    result = await orchestrator.handle(state["input"])
    return {"output": result}

# Build a minimal StateGraph
workflow = StateGraph(AgentState)
workflow.add_node("agent", run_orchestrator)
workflow.add_edge(START, "agent")
workflow.add_edge("agent", END)

# Compile into a graph object that langgraph-cli expects
graph = workflow.compile()

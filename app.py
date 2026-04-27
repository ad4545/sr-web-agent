import json
import asyncio
import streamlit as st
from dotenv import load_dotenv

# Must load env before any agent imports touch genai
load_dotenv()

from core.orchestrator import Orchestrator
from map.graph import NODES

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="AMR Navigation Agent",
    page_icon="🤖",
    layout="wide",
)

# ── Custom CSS (Modern styling) ──────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    
    .main-header {
        background: linear-gradient(135deg, #1e1b4b, #312e81);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        color: white;
    }
    
    .status-box {
        padding: 1rem;
        border-radius: 8px;
        background: #f1f5f9;
        margin-bottom: 1rem;
        border-left: 5px solid #6366f1;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🤖 AMR Navigation Agent v2</h1>
    <p>Modernized Fleet Orchestration with Python 3.14+ target</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.title("🗺️ Map Registry")
    st.info("Available Warehouse Nodes:")
    destinations = [n for n in NODES.keys() if not n.startswith("D") or "WP" not in n]
    for n in sorted(destinations):
        st.write(f"- {n}")

@st.cache_resource
def get_orchestrator():
    return Orchestrator()

orchestrator = get_orchestrator()

# ── Async Processing ─────────────────────────────────────────
async def run_orchestration(query: str):
    with st.status("⚡ Orchestrating AMR...", expanded=True) as status:
        final_result = None
        async for event in orchestrator.handle_streaming(query):
            if event.message:
                st.write(event.message)
            if event.stage == "complete":
                final_result = event.data
        
        if final_result:
            status.update(label="✅ Task Planned", state="complete", expanded=False)
        else:
            status.update(label="⚠️ Planning Failed", state="error")
        return final_result

# ── Chat Interface ───────────────────────────────────────────
query = st.chat_input("Command the robot (e.g. 'Navigate to DESK_1')")

if query:
    st.chat_message("user").write(query)
    
    # Execute the async loop
    result_data = asyncio.run(run_orchestration(query))
    
    if result_data:
        with st.chat_message("assistant"):
            st.success(result_data.get("summary", "Done."))
            if master_task := result_data.get("master_task"):
                with st.expander("📋 Master Task Details", expanded=True):
                    st.json(master_task)
                    st.download_button(
                        "Download Task JSON",
                        json.dumps(master_task, indent=2),
                        f"task_{master_task['masterTaskName']}.json",
                        "application/json"
                    )

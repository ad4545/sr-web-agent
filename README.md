# Industrial AMR Navigation Agent

A professional, scalable, and modular navigation system for Autonomous Mobile Robots (AMRs) in warehouse environments. This system uses a multi-agent orchestrator pattern to handle complex navigation tasks with industrial-grade reliability.

## 🏗️ Architecture Overview

The system is built on a **modular agent-tool architecture**, separating intent parsing, pathfinding logic, and UI orchestration.

### Core Components
- **Orchestrator (`core/orchestrator.py`)**: The central brain that routes user requests to the appropriate agent and manages the execution lifecycle.
- **Navigation Agent (`agents/navigation_agent.py`)**: A specialized agent that uses Gemini Flash 2.5 to parse user intent and synthesize final mission plans.
- **Navigation Tool (`tools/navigation.py`)**: Implements Dijkstra's algorithm to find the shortest path based strictly on the warehouse graph.
- **Map Registry (`map/`)**: Manages the warehouse layout.
    - `mongo_loader.py`: Fetches real-time waypoint and connectivity data from MongoDB.
    - `graph.py`: Builds the adjacency list for pathfinding, incorporating industrial constraints.

## ⚙️ Industrial Configuration

To ensure safety and reliability, the AMR's starting position and its initial connectivity are **hardcoded** and must be reviewed by an engineer before deployment.

### Configuring the Start Node
Open `map/graph.py` to modify the origin connections:
```python
# --- AMR START CONFIGURATION ---
START_NODE_NEIGHBOURS = ["wp-01", "dummy02"]
VIRTUAL_START_NAME = "VIRTUAL_START"
VIRTUAL_START_COORD = (0.0, 0.0, 0.0)
# -------------------------------
```
The system will strictly follow these edges. If a destination is requested, the robot will find the shortest path starting from `VIRTUAL_START` through one of these allowed neighbors.

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.14+
- `uv` for dependency management
- MongoDB instance (Waypoints collection)
- Google Gemini API Key

### 2. Installation
```bash
uv sync
```

### 3. Execution
Run the interactive Streamlit dashboard:
```bash
uv run streamlit run app.py
```

## 🛠️ Scalability & Extensions

### Adding New Agents
1. Create a new class in `agents/` inheriting from `BaseAgent`.
2. Implement `run` and `run_streaming`.
3. Register the agent in `Orchestrator.__init__`.

### Adding New Tools
1. Create a new class in `tools/` inheriting from `BaseTool`.
2. Implement the `execute` method.
3. Pass the tool instance to the relevant agent.

## 📄 Mission Structure (JSON)
The agent generates a standardized **Master Task** JSON for robot consumption:
- `masterTaskName`: Unique mission ID.
- `tasks`: A sequence of `Move` tasks.
- `paths`: Coordinates (translation/rotation) for each waypoint in the leg.

---
*Designed for Industrial Reliability and Scalable Fleet Management.*

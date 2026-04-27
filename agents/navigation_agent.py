import json
import logging
from typing import AsyncGenerator, Optional
from google import genai
from google.genai import types

from core.base_agent import BaseAgent
from core.events import ProgressEvent
from tools.navigation import NavigationTool
from tools.kafka_tool import KafkaTaskTool
from map.graph import get_node_registry, get_amr_start

logger = logging.getLogger(__name__)

def get_intent_prompt():
    from map.graph import get_node_registry
    nodes, _ = get_node_registry()
    map_data = json.dumps({name: coord for name, coord in nodes.items()}, indent=2)
    return (
        "You are an expert intent parser for a warehouse Autonomous Mobile Robot (AMR).\n"
        f"Available Map Registry (Canonical Node Name: Coordinates):\n{map_data}\n\n"
        "Your mission is to extract the sequence of destinations from the user's message.\n"
        "RULES:\n"
        "1. Map user-provided names to the CLOSEST matching Canonical Node Name from the Registry (even if there are typos or case differences).\n"
        "2. If the user provides multiple locations, list them in the order they should be visited.\n\n"
        "Respond with ONLY a raw JSON object:\n"
        '  {"destinations": ["NODE_A", "NODE_B"], "start_coordinate": {"x": 0, "y": 0, "z": 0}}\n'
        "Include 'start_coordinate' ONLY if the user explicitly specifies a starting location like 'start at 0,0,0'."
    )

def get_synthesis_prompt():
    return (
        "You are a professional warehouse fleet dispatcher.\n"
        "Review the calculated navigation data and provide a concise, reassuring summary to the operator.\n"
        "Mention the sequence of nodes and the total distance if possible.\n"
        "Respond with ONLY a raw JSON object:\n"
        '  {"summary": "Your dispatcher message here"}'
    )

class NavigationAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.nav_tool = NavigationTool()
        self.kafka_tool = KafkaTaskTool()

    @property
    def name(self) -> str:
        return "NavigationAgent"

    @property
    def description(self) -> str:
        return "Specialized in calculating optimal paths for AMRs within the warehouse floor."

    def _get_client(self):
        from core.config import config
        return genai.Client(api_key=config.GEMINI_API_KEY)

    async def _llm_parse_intent(self, task: str) -> dict:
        with self._get_client() as client:
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=task,
                config=types.GenerateContentConfig(
                    system_instruction=get_intent_prompt(),
                    response_mime_type="application/json"
                ),
            )
            return json.loads(response.text)

    async def _llm_synthesise(self, nav_data_list: list) -> dict:
        prompt = f"Calculated trajectories for the following legs:\n{json.dumps(nav_data_list, indent=2)}"
        with self._get_client() as client:
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=get_synthesis_prompt(),
                    response_mime_type="application/json"
                ),
            )
            return json.loads(response.text)

    async def run(self, task: str) -> dict:
        intent = await self._llm_parse_intent(task)
        destinations = intent.get("destinations", [])
        start_coord = intent.get("start_coordinate")

        if not destinations:
            return {"text": intent.get("reply", "I can only handle navigation requests."), "data": None, "master_task": None}

        nav_data_list = []
        current_start_node = None
        current_start_coord = start_coord if start_coord else {"x": 0.0, "y": 0.0, "z": 0.0}

        for dest in destinations:
            nav_data = self.nav_tool.execute(
                destination_name=dest,
                start_node=current_start_node,
                start_coordinate=current_start_coord
            )
            if "error" in nav_data:
                return {"text": nav_data["error"], "data": None, "master_task": None}
            
            nav_data_list.append(nav_data)
            current_start_node = nav_data["destination"]
            current_start_coord = None 

        synthesis = await self._llm_synthesise(nav_data_list)
        master_task = _build_master_task(nav_data_list)
        
        # Send to Kafka
        self.kafka_tool.execute(task_json=master_task)
        
        return {"text": synthesis.get("summary", "Done."), "data": nav_data_list, "master_task": master_task}

    async def run_streaming(self, task: str) -> AsyncGenerator:
        yield ProgressEvent(stage="llm_intent", message="Analyzing navigation request...", agent_id=self.name)
        try:
            intent = await self._llm_parse_intent(task)
        except Exception as e:
            yield ProgressEvent(stage="agent_error", message=f"Intent parsing failed: {e}", agent_id=self.name)
            return

        destinations = intent.get("destinations", [])
        start_coord = intent.get("start_coordinate")

        if not destinations:
            yield ProgressEvent(stage="complete", message=intent.get("reply", "I can only handle navigation requests."), agent_id=self.name)
            return

        yield ProgressEvent(stage="llm_intent", message=f"Target sequence confirmed: {' → '.join(destinations)}", agent_id=self.name)
        nav_data_list = []
        current_start_node = None
        current_start_coord = start_coord if start_coord else {"x": 0.0, "y": 0.0, "z": 0.0}
        
        for dest in destinations:
            display_start = current_start_node if current_start_node else f"Coord({current_start_coord['x']}, {current_start_coord['y']})"
            yield ProgressEvent(stage="tool_call", message=f"Calculating trajectory: {display_start} → {dest}...", agent_id=self.name)
            
            nav_data = self.nav_tool.execute(
                destination_name=dest,
                start_node=current_start_node,
                start_coordinate=current_start_coord
            )
            
            if "error" in nav_data:
                yield ProgressEvent(stage="tool_error", message=nav_data["error"], agent_id=self.name)
                return
            
            nav_data_list.append(nav_data)
            current_start_node = nav_data["destination"]
            current_start_coord = None

        yield ProgressEvent(stage="kafka_send", message="Building mission plan...", agent_id=self.name)
        master_task = _build_master_task(nav_data_list)
        
        yield ProgressEvent(stage="kafka_send", message="Sending task to Industrial AMR via Kafka...", agent_id=self.name)
        kafka_result = self.kafka_tool.execute(task_json=master_task)
        
        if "error" in kafka_result:
             yield ProgressEvent(stage="tool_error", message=kafka_result["error"], agent_id=self.name)
             return
        
        # The user wants the last message to be confirmation of task sent
        yield ProgressEvent(
            stage="agent_done",
            message="Task has been sent to the robot fleet.",
            data={
                "text": "Task has been sent to the robot fleet.",
                "summary": "Task has been sent to the robot fleet.",
                "master_task": master_task
            },
            agent_id=self.name
        )

def _build_master_task(nav_data_list: list) -> dict:
    import uuid
    from datetime import datetime, timezone
    
    tasks = []
    for leg in nav_data_list:
        waypoints = leg.get("waypoints", [])
        json_paths = [
            {
                "translation": {
                    "x": wp["coordinate"][0],
                    "y": wp["coordinate"][1],
                    "z": wp["coordinate"][2],
                },
                "rotation": {"x": 0, "y": 0, "z": 0, "w": 1},
            }
            for wp in waypoints
        ]
        
        tasks.append({
            "taskName": "Move",
            "type": "Path",
            "path": {
                "_id": uuid.uuid4().hex[:24],
                "pathName": f"path-to-{leg['destination']}",
                "paths": json_paths,
                "createdAt": datetime.now(timezone.utc).isoformat()
            }
        })
        
    return {
        "masterTaskName": f"task-{uuid.uuid4().hex[:8]}",
        "tasks": tasks
    }
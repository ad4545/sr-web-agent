import json
from typing import AsyncGenerator, Dict

from core.base_agent import BaseAgent
from core.events import ProgressEvent
from agents.navigation_agent import NavigationAgent

class Orchestrator:
    """
    Top-level orchestrator for the system.
    Maintains a registry of agents and routes user queries to the appropriate agent.
    If multiple agents existed, an LLM routing call could be added here.
    """

    def __init__(self):
        print("[Orchestrator] Initializing Core...")
        
        self.agents: Dict[str, BaseAgent] = {}
        # Register available agents
        self.register_agent(NavigationAgent())
        
        # Default agent for all queries currently
        self.default_agent = self.agents.get("NavigationAgent")
        
        if not self.default_agent:
            raise RuntimeError("NavigationAgent failed to initialize or register.")
            
        print(f"[Orchestrator] Ready. Loaded {len(self.agents)} agents.")

    def register_agent(self, agent: BaseAgent):
        """Register an agent into the orchestrator."""
        self.agents[agent.name] = agent

    def _route_query(self, user_message: str) -> BaseAgent:
        """
        Determine which agent to send the query to.
        Currently defaults to NavigationAgent. In the future, this will use
        an LLM to select the agent based on agent.description.
        """
        return self.default_agent

    async def handle(self, user_message: str) -> str:
        """CLI entry point. Non-streaming."""
        print(f"\n[Orchestrator] → '{user_message}'")
        
        agent = self._route_query(user_message)
        result = await agent.run(user_message)
        
        if master_task := result.get("master_task"):
            return json.dumps(master_task, indent=4)
            
        return result.get("text", "No response.")

    async def handle_streaming(self, user_message: str) -> AsyncGenerator[ProgressEvent, None]:
        """Async generator for UI clients — routes request and forwards events."""
        agent = self._route_query(user_message)
        agent_result = None
        
        async for event in agent.run_streaming(user_message):
            yield event
            if event.stage == "agent_done":
                agent_result = event.data

        if agent_result and agent_result.get("master_task"):
            yield ProgressEvent(
                stage="complete",
                message="",
                data={
                    "summary": agent_result.get("text", ""),
                    "master_task": agent_result["master_task"],
                },
                agent_id="Orchestrator"
            )
        else:
            yield ProgressEvent(
                stage="complete",
                message="",
                data={
                    "summary": (agent_result or {}).get("text", "No result.") if agent_result else "No result.",
                    "master_task": None,
                },
                agent_id="Orchestrator"
            )

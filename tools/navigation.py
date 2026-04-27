import heapq
import json
import logging
from typing import Any, Optional, Dict

from map.graph import get_node_registry, get_amr_start, build_graph
from core.base_tool import BaseTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

type Coordinate = tuple[float, float, float]
type PathResult = dict[str, Any]

class NavigationTool(BaseTool):
    """
    Tool for navigating the AMR around the warehouse using Dijkstra's algorithm.
    """
    
    @property
    def name(self) -> str:
        return "find_shortest_path"
        
    @property
    def description(self) -> str:
        return "Calculates the shortest route to a specific destination in the warehouse using Dijkstra's algorithm."
        
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Interface for BaseTool.
        """
        destination_name = kwargs.get("destination_name")
        start_node = kwargs.get("start_node")
        start_coord = kwargs.get("start_coordinate")
        dest_coord = kwargs.get("destination_coordinate")
        
        # Helper handling for dict coordinates
        def to_tuple(c):
            if isinstance(c, dict):
                return (float(c.get("x", 0.0)), float(c.get("y", 0.0)), float(c.get("z", 0.0)))
            return c

        return self._find_shortest_path(
            destination_name=destination_name,
            start_node=start_node,
            start_coordinate=to_tuple(start_coord),
            destination_coordinate=to_tuple(dest_coord)
        )

    def _find_nearest_node(self, target_coord: Coordinate) -> str:
        """Finds the node in the current map closest to the given coordinate."""
        nodes, _ = get_node_registry()
        if not nodes:
            return ""
            
        best_node = list(nodes.keys())[0]
        min_dist = float('inf')
        
        for node, coord in nodes.items():
            dist = sum((a - b)**2 for a, b in zip(target_coord, coord))
            if dist < min_dist:
                min_dist = dist
                best_node = node
        return best_node

    def _find_shortest_path(
        self,
        destination_name: Optional[str] = None, 
        start_node: Optional[str] = None,
        start_coordinate: Optional[Coordinate] = None,
        destination_coordinate: Optional[Coordinate] = None
    ) -> PathResult:
        """
        Finds the shortest path using Dijkstra's algorithm.
        """
        nodes, _ = get_node_registry()
        if not nodes:
            return {"error": "No map data available. Please check MongoDB connection."}

        # Create a mapping of uppercase names to original names for case-insensitive lookup
        name_map = {name.upper(): name for name in nodes.keys()}
        
        # 1. Resolve starting point
        if start_coordinate:
            # Check if it's the origin (0,0,0) - prioritize VIRTUAL_START
            if all(c == 0.0 for c in start_coordinate):
                start_node = "VIRTUAL_START"
                logger.info("Starting from origin. Using VIRTUAL_START.")
            else:
                start_node = self._find_nearest_node(start_coordinate)
                logger.info("Starting from coordinate %s. Nearest node: %s", start_coordinate, start_node)
        elif start_node:
            # Case-insensitive lookup for start node
            if start_node.upper() in name_map:
                start_node = name_map[start_node.upper()]
        else:
            start_node = get_amr_start()

        if not start_node or start_node not in nodes:
            return {"error": f"Starting node '{start_node}' not found in map."}

        # 2. Resolve destination node
        if destination_coordinate:
            is_placeholder = all(c == 0.0 for c in destination_coordinate)
            if not is_placeholder:
                destination_name = self._find_nearest_node(destination_coordinate)
                logger.info("Mapped coordinate %s to nearest node: %s", destination_coordinate, destination_name)

        if not destination_name:
            return {"error": "No destination provided."}
            
        # Case-insensitive lookup for destination
        if destination_name.upper() in name_map:
            destination_name = name_map[destination_name.upper()]
        
        if destination_name not in nodes:
            return {"error": f"Destination '{destination_name}' not found in map registry."}
        
        # 3. Build graph
        graph = build_graph()

        # 4. Dijkstra's Algorithm
        distances = {node: float('inf') for node in nodes}
        distances[start_node] = 0.0
        predecessors: dict[str, Optional[str]] = {node: None for node in nodes}
        
        pq: list[tuple[float, str]] = [(0.0, start_node)]
        visited: set[str] = set()

        while pq:
            current_distance, current_node = heapq.heappop(pq)
            if current_node in visited: continue
            visited.add(current_node)
            
            if current_node == destination_name: break
                
            for neighbor, weight in graph.get(current_node, []):
                if neighbor in visited: continue
                new_distance = current_distance + weight
                if neighbor in distances and new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    predecessors[neighbor] = current_node
                    heapq.heappush(pq, (new_distance, neighbor))
                    
        if distances[destination_name] == float('inf'):
            return {"error": f"No path found from '{start_node}' to '{destination_name}'."}
            
        # 5. Reconstruct path
        path: list[str] = []
        curr: Optional[str] = destination_name
        while curr is not None:
            path.append(curr)
            curr = predecessors[curr]
        path.reverse()
        
        # 6. Format output
        # Omit current position (start of the leg)
        waypoints = []
        
        if len(path) > 1:
            output_nodes = path[1:]
        elif len(path) == 1:
            if start_coordinate and not all(c == p for c, p in zip(start_coordinate, nodes[path[0]])):
                output_nodes = [path[0]]
            else:
                output_nodes = []
        else:
            output_nodes = []

        waypoints = [{"name": name, "coordinate": nodes[name]} for name in output_nodes]
        
        return {
            "start": start_node,
            "destination": destination_name,
            "path": output_nodes,
            "distance": round(distances[destination_name], 4),
            "waypoints": waypoints
        }

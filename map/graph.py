import math
import logging
import json
from typing import Dict, List, Tuple

from map.mongo_loader import fetch_nodes_from_mongo

# ==============================================================================
# INDUSTRIAL AMR - HARDCODED CONFIGURATION
# ==============================================================================
# The start node is a virtual origin (0,0,0) not present in MongoDB.
# Define its physically connected neighbors here before any warehouse changes.
START_NODE_NEIGHBOURS = ["wp-01", "wp-05"]
VIRTUAL_START_NAME = "VIRTUAL_START"
VIRTUAL_START_COORD = (0.0, 0.0, 0.0)
# ==============================================================================

def get_map_data():
    """Fetches nodes and connectivity directly from MongoDB. No fallbacks."""
    nodes_db, connectivity_db = fetch_nodes_from_mongo()
    
    if not nodes_db:
        logger = logging.getLogger(__name__)
        logger.error("No map data found in MongoDB. Navigation will be unavailable.")
        return {}, {}
        
    return nodes_db, connectivity_db

def get_node_registry() -> Tuple[Dict[str, Tuple[float, float, float]], Dict[str, List[str]]]:
    """Returns the full node set and connectivity, including the VIRTUAL_START."""
    nodes, connectivity = get_map_data()
    
    # Inject VIRTUAL_START into the registry
    full_nodes = nodes.copy()
    full_nodes[VIRTUAL_START_NAME] = VIRTUAL_START_COORD
    
    full_connectivity = connectivity.copy()
    full_connectivity[VIRTUAL_START_NAME] = START_NODE_NEIGHBOURS
    
    return full_nodes, full_connectivity

# Compatibility layer for legacy components
NODES, CONNECTIVITY = get_node_registry()

def get_amr_start():
    """Returns the canonical starting node for all missions."""
    return VIRTUAL_START_NAME

def get_distance(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> float:
    """Calculates Euclidean distance between two 3D points."""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2 + (p1[2] - p2[2]) ** 2)

def build_graph() -> Dict[str, List[Tuple[str, float]]]:
    """
    Builds the adjacency list for Dijkstra's algorithm.
    Rely strictly on the connectivity (neighbours) defined in MongoDB + VIRTUAL_START.
    """
    nodes, connectivity = get_node_registry()
    graph: Dict[str, List[Tuple[str, float]]] = {node: [] for node in nodes}
    
    # Add baseline connectivity (Strictly follows 'neighbour' field + hardcoded start)
    for node, neighbors in connectivity.items():
        if node not in nodes: continue
        p1 = nodes[node]
        for neighbor in neighbors:
            if neighbor not in nodes: continue
            p2 = nodes[neighbor]
            dist = get_distance(p1, p2)
            graph[node].append((neighbor, round(dist, 4)))
            
            # Ensure bidirectional connectivity for the virtual start if it appears as a neighbor
            if node == VIRTUAL_START_NAME:
                if VIRTUAL_START_NAME not in [n for n, _ in graph[neighbor]]:
                    graph[neighbor].append((VIRTUAL_START_NAME, round(dist, 4)))
                    
    return graph

if __name__ == "__main__":
    # Diagnostic tool to inspect the generated graph
    print(f"AMR Home Origin: {VIRTUAL_START_NAME} {VIRTUAL_START_COORD}")
    print(f"Industrial Connections: {START_NODE_NEIGHBOURS}")
    print("\n--- Computed Graph Weights ---")
    g = build_graph()
    for n, edges in g.items():
        if edges:
            print(f"{n}:")
            for neighbor, weight in sorted(edges):
                print(f"  -> {neighbor} (Dist: {weight})")

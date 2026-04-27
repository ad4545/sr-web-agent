from map.graph import build_graph, NODES, CONNECTIVITY

def inspect_full_graph():
    """
    Utility script to display the entire warehouse graph.
    Shows each node, its coordinates, and all its connections (topological + proximity shortcuts).
    """
    print("=" * 80)
    print(f"{'WAREHOUSE GRAPH INSPECTION':^80}")
    print("=" * 80)
    
    graph = build_graph()
    
    for node in sorted(graph.keys()):
        coord = NODES.get(node, (0, 0, 0))
        print(f"\nNODE: {node} (x: {coord[0]:.2f}, y: {coord[1]:.2f}, z: {coord[2]:.2f})")
        
        # Get edges for this node
        edges = graph.get(node, [])
        
        if not edges:
            print("  (No connections)")
            continue
            
        print("  CONNECTIONS:")
        # Sort edges by neighbor name for consistent output
        for neighbor, distance in sorted(edges):
            # Check if it's a primary topological neighbor or a proximity shortcut
            is_primary = neighbor in CONNECTIVITY.get(node, [])
            type_str = "[Primary]" if is_primary else "[Shortcut]"
            print(f"    -> {neighbor:<12} | Distance: {distance:<8.4f} | {type_str}")

if __name__ == "__main__":
    try:
        inspect_full_graph()
    except Exception as e:
        print(f"Error during graph inspection: {e}")

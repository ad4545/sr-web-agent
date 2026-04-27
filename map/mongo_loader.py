import logging
from pymongo import MongoClient
from core.config import config

logger = logging.getLogger(__name__)

def fetch_nodes_from_mongo():
    """
    Fetches nodes from MongoDB and transforms them into the format expected by the navigation system.
    
    Expected MongoDB Document Structure:
    {
        "waypointName": "wp-01",
        "cords": [
          {
            "translation": { "x": 4.1728994905093995, "y": 0.8326006769038756, "z": 0 },
            "rotation": { "x": 0, "y": 0, "z": 0, "w": 1 }
          }
        ],
        "neighbour": [ "wp-02", "wp-03", "dummy01" ]
    }
    """
    nodes = {}
    connectivity = {}
    
    try:
        client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[config.MONGO_DB_NAME]
        collection = db[config.MONGO_COLLECTION_NAME]
        
        cursor = collection.find({})
        docs = list(cursor)
        
        if not docs:
            logger.warning("No nodes found in MongoDB collection '%s.%s'", config.MONGO_DB_NAME, config.MONGO_COLLECTION_NAME)
            return {}, {}
            
        for doc in docs:
            name = doc.get("waypointName")
            if not name:
                continue
                
            # Extract coordinates from cords[0].translation
            cords_list = doc.get("cords", [])
            if cords_list and isinstance(cords_list, list):
                translation = cords_list[0].get("translation", {})
                x = translation.get("x", 0.0)
                y = translation.get("y", 0.0)
                z = translation.get("z", 0.0)
                nodes[name] = (float(x), float(y), float(z))
            
            # Extract neighbors
            neighbors = doc.get("neighbour", [])
            if neighbors and isinstance(neighbors, list):
                connectivity[name] = neighbors
                
        logger.info("Successfully loaded %d nodes from MongoDB", len(nodes))
        return nodes, connectivity
        
    except Exception as e:
        logger.error("Failed to fetch nodes from MongoDB: %s", e)
        # Return empty structures; the graph.py will handle the fallback or error
        return {}, {}

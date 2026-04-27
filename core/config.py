import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory is one level up from core/ (i.e. the project root)
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH, override=True)

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    MAX_PROXIMITY_THRESHOLD = 3.2
    
    # MongoDB Config
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://16.112.194.71:27017")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "sevenhub")
    MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "waypoints")
    
    # Kafka Config
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "task-5")
    
    @classmethod
    def validate(cls):
        if not cls.GEMINI_API_KEY:
            raise RuntimeError(f"GEMINI_API_KEY is not set. Please add it to {ENV_PATH}")
        if not cls.MONGO_URI:
            raise RuntimeError(f"MONGO_URI is not set. Please add it to {ENV_PATH}")

# Validate eagerly if imported
config = Config()

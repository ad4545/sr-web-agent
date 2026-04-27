import json
import logging
from typing import Any, Dict
from confluent_kafka import Producer

from core.base_tool import BaseTool
from core.config import config

logger = logging.getLogger(__name__)

class KafkaTaskTool(BaseTool):
    """
    Tool for sending mission tasks to a Kafka topic for robot consumption.
    """
    
    def __init__(self):
        super().__init__()
        # Lazy initialization of the producer to avoid connection errors if Kafka is offline
        self._producer = None

    @property
    def name(self) -> str:
        return "send_task"

    @property
    def description(self) -> str:
        return "Sends a finalized master task JSON to a Kafka topic for industrial AMR execution."

    @property
    def producer(self):
        if self._producer is None:
            try:
                self._producer = Producer({
                    'bootstrap.servers': config.KAFKA_BOOTSTRAP_SERVERS,
                    'client.id': 'amr-nav-agent'
                })
            except Exception as e:
                logger.error(f"Failed to create Kafka producer: {e}")
                raise
        return self._producer

    def _delivery_report(self, err, msg):
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Sends the task JSON to Kafka.
        Args:
            task_json (dict): The master task JSON to send.
        """
        task_json = kwargs.get("task_json")
        if not task_json:
            return {"error": "No task_json provided to send_task tool."}

        try:
            p = self.producer
            payload = json.dumps(task_json).encode('utf-8')
            
            p.produce(
                config.KAFKA_TOPIC, 
                value=payload, 
                callback=self._delivery_report
            )
            
            # Flush to ensure the message is sent (Synchronous flush for reliability)
            p.flush(timeout=10.0)
            
            return {
                "status": "success",
                "message": f"Task successfully sent to topic: {config.KAFKA_TOPIC}",
                "topic": config.KAFKA_TOPIC
            }
        except Exception as e:
            logger.error(f"Kafka Execution Error: {e}")
            return {"error": f"Failed to send task to Kafka: {str(e)}"}

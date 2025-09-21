import os
import json
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from google.cloud import pubsub_v1
from dotenv import load_dotenv

from app.shared_crew_lib.clients import gcp_clients
from app.shared_crew_lib.agents.omni_agent import OmniAgent
from app.shared_crew_lib.schemas.agent_task_message import AgentTaskMessage

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variables
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
AGENT_SUBSCRIPTION_ID = os.getenv("AGENT_SUBSCRIPTION_ID")

if not all([PROJECT_ID, AGENT_SUBSCRIPTION_ID]):
    raise RuntimeError("Required environment variables not set: GCP_PROJECT_ID, AGENT_SUBSCRIPTION_ID")

# Initialize clients
subscriber = gcp_clients.get_subscriber_client()
db = gcp_clients.get_firestore_client()

class OmniAgentWorker:
    """OmniAgent Worker - Handles configurable general tasks"""
    
    def __init__(self):
        self.subscription_path = subscriber.subscription_path(PROJECT_ID, AGENT_SUBSCRIPTION_ID)
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    async def process_message(self, message):
        """Process individual message"""
        try:
            # Parse message
            message_data = json.loads(message.data.decode('utf-8'))
            
            # Check if this is a registry update message
            if message.attributes.get('message_type') == 'registry_update':
                await self._handle_registry_update(message_data)
                message.ack()
                return
            
            task_message = AgentTaskMessage(**message_data)
            
            logger.info(f"Processing OmniAgent task: {task_message.task_id}")
            
            # Extract configuration parameters from task data
            input_data = task_message.input_data
            custom_role = input_data.get('custom_role', 'General Assistant')
            custom_goal = input_data.get('custom_goal', 'Assist users with various tasks')
            custom_backstory = input_data.get('custom_backstory', 'You are a flexible AI assistant capable of adapting to various task requirements.')
            
            # Create OmniAgent instance
            agent = OmniAgent(
                task_id=task_message.task_id,
                output_field="omni_agent_output",
                custom_role=custom_role,
                custom_goal=custom_goal,
                custom_backstory=custom_backstory
            )
            
            # Save current agent instance for handling registry updates
            self.current_agent = agent
            
            # Execute task
            result = await agent.run(task_message.task_id, input_data)
            
            if result.get("status") == "COMPLETED":
                logger.info(f"OmniAgent task completed: {task_message.task_id}")
                message.ack()
            else:
                logger.error(f"OmniAgent task failed: {task_message.task_id}, error: {result.get('error')}")
                message.nack()
                
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            message.nack()
    
    async def _handle_registry_update(self, message_data):
        """Handle agent registry update"""
        try:
            # Update local agent registry
            if hasattr(self, 'current_agent') and self.current_agent:
                self.current_agent.handle_registry_update(message_data)
            
            logger.info(f"OmniAgent Worker handled registry update: {message_data.get('event_type')}")
            
        except Exception as e:
            logger.error(f"Registry update handling failed: {e}")
    
    def message_callback(self, message):
        """Pub/Sub message callback"""
        # Use asyncio to run async processing function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.process_message(message))
        finally:
            loop.close()
    
    def start_listening(self):
        """Start listening for messages"""
        logger.info(f"OmniAgent Worker starting to listen: {self.subscription_path}")
        
        # Configure flow control
        flow_control = pubsub_v1.types.FlowControl(max_messages=10)
        
        # Start pulling messages
        streaming_pull_future = subscriber.subscribe(
            self.subscription_path,
            callback=self.message_callback,
            flow_control=flow_control
        )
        
        logger.info("OmniAgent Worker is running...")
        
        try:
            streaming_pull_future.result()
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            logger.info("OmniAgent Worker stopped")

def main():
    """Main function"""
    worker = OmniAgentWorker()
    worker.start_listening()

if __name__ == "__main__":
    main()

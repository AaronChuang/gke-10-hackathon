import os
import json
import asyncio
import logging
from typing import Dict, Any
from google.cloud import pubsub_v1
from dotenv import load_dotenv

from app.shared_crew_lib.clients import gcp_clients

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variables
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
REGISTRY_SUBSCRIPTION_ID = os.getenv("AGENT_REGISTRY_SUBSCRIPTION_ID", "agent-registry-updates-sub")

if not PROJECT_ID:
    raise RuntimeError("Required environment variable not set: GCP_PROJECT_ID")

# Initialize clients
subscriber = gcp_clients.get_subscriber_client()
db = gcp_clients.get_firestore_client()

class AgentRegistryListener:
    """Agent Registry Listener"""
    
    def __init__(self):
        self.subscription_path = subscriber.subscription_path(PROJECT_ID, REGISTRY_SUBSCRIPTION_ID)
        self.local_agent_registry = {}
        
    async def initialize_local_registry(self):
        """Initialize local agent registry"""
        try:
            agents_ref = db.collection("agents")
            agents = agents_ref.where("status", "==", "ACTIVE").stream()
            
            for agent in agents:
                agent_data = agent.to_dict()
                self.local_agent_registry[agent_data["agent_id"]] = agent_data
                
            logger.info(f"Initialized local registry, loaded {len(self.local_agent_registry)} agents")
            
        except Exception as e:
            logger.error(f"Failed to initialize local registry: {e}")
    
    async def process_registry_update(self, message):
        """Process registry update message"""
        try:
            # Parse message
            message_data = json.loads(message.data.decode('utf-8'))
            action = message_data.get("action")
            agent_data = message_data.get("agent_data", {})
            
            logger.info(f"Processing registry update: {action} - {agent_data.get('agent_id', 'unknown')}")
            
            if action == "AGENT_ADDED":
                await self._handle_agent_added(agent_data)
            elif action == "AGENT_REMOVED":
                await self._handle_agent_removed(agent_data)
            elif action == "AGENT_UPDATED":
                await self._handle_agent_updated(agent_data)
            else:
                logger.warning(f"Unknown registry update action: {action}")
            
            message.ack()
            
        except Exception as e:
            logger.error(f"Failed to process registry update: {e}")
            message.nack()
    
    async def _handle_agent_added(self, agent_data: Dict[str, Any]):
        """Handle agent addition"""
        agent_id = agent_data.get("agent_id")
        if agent_id:
            self.local_agent_registry[agent_id] = agent_data
            logger.info(f"Added agent to local registry: {agent_id}")
            
            # Notify all agents that a new agent has joined
            await self._broadcast_to_all_agents("PEER_AGENT_ADDED", agent_data)
    
    async def _handle_agent_removed(self, agent_data: Dict[str, Any]):
        """Handle agent removal"""
        agent_id = agent_data.get("agent_id")
        if agent_id and agent_id in self.local_agent_registry:
            del self.local_agent_registry[agent_id]
            logger.info(f"Removed agent from local registry: {agent_id}")
            
            # Notify all agents that an agent has been removed
            await self._broadcast_to_all_agents("PEER_AGENT_REMOVED", {"agent_id": agent_id})
    
    async def _handle_agent_updated(self, agent_data: Dict[str, Any]):
        """Handle agent update"""
        agent_id = agent_data.get("agent_id")
        if agent_id:
            self.local_agent_registry[agent_id] = agent_data
            logger.info(f"Updated agent in local registry: {agent_id}")
            
            # Notify all agents that an agent has been updated
            await self._broadcast_to_all_agents("PEER_AGENT_UPDATED", agent_data)
    
    async def _broadcast_to_all_agents(self, event_type: str, data: Dict[str, Any]):
        """Broadcast event to all agents"""
        try:
            publisher = gcp_clients.get_publisher_client()
            
            broadcast_message = {
                "event_type": event_type,
                "data": data,
                "registry_snapshot": list(self.local_agent_registry.keys())
            }
            
            # Send message to each agent's topic
            for agent_id in self.local_agent_registry.keys():
                try:
                    topic_path = publisher.topic_path(PROJECT_ID, f"{agent_id}-topic")
                    
                    future = publisher.publish(
                        topic_path,
                        json.dumps(broadcast_message).encode('utf-8'),
                        message_type="registry_update"
                    )
                    
                    future.result()  # Wait for completion
                    
                except Exception as e:
                    logger.warning(f"Failed to broadcast to agent {agent_id}: {e}")
            
            logger.info(f"Broadcast event completed: {event_type}")
            
        except Exception as e:
            logger.error(f"Failed to broadcast event: {e}")
    
    def message_callback(self, message):
        """Pub/Sub message callback"""
        # Use asyncio to run async processing function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.process_registry_update(message))
        finally:
            loop.close()
    
    def start_listening(self):
        """Start listening for registry updates"""
        logger.info(f"Agent registry listener starting to listen: {self.subscription_path}")
        
        # Configure flow control
        flow_control = pubsub_v1.types.FlowControl(max_messages=10)
        
        # Start pulling messages
        streaming_pull_future = subscriber.subscribe(
            self.subscription_path,
            callback=self.message_callback,
            flow_control=flow_control
        )
        
        logger.info("Agent registry listener is running...")
        
        try:
            streaming_pull_future.result()
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            logger.info("Agent registry listener stopped")

async def main():
    """Main function"""
    listener = AgentRegistryListener()
    
    # Initialize local registry
    await listener.initialize_local_registry()
    
    # Start listening
    listener.start_listening()

if __name__ == "__main__":
    asyncio.run(main())

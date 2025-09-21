from typing import List, Optional
import logging
from ..schemas.agent_registry import AgentRegistryEntry, AgentStatus
from .agent_initialization_service import AgentInitializationService
from ..clients import gcp_clients
from datetime import datetime

logger = logging.getLogger(__name__)

class AgentRegistryService:
    """Agent Registry Service - Manages dynamic Agent creation and discovery"""
    
    def __init__(self):
        self.db = None
        self.collection_name = "agents"
        self.initialization_service = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        try:
            self.db = gcp_clients.get_firestore_client()
            if self.db is None:
                raise RuntimeError("Failed to initialize Firestore client")
            
            self.initialization_service = AgentInitializationService()
            logger.info("AgentRegistryService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AgentRegistryService: {e}")
            raise
    
    async def get_all_agents(self) -> List[AgentRegistryEntry]:
        """Get all registered agents"""
        try:
            docs = self.db.collection(self.collection_name).stream()
            agents = []
            
            for doc in docs:
                agent_data = doc.to_dict()
                agents.append(AgentRegistryEntry(**agent_data))
            
            return agents
        except Exception as e:
            logger.error(f"Failed to get agents list: {e}")
            return []
    
    async def get_active_agents(self) -> List[AgentRegistryEntry]:
        """Get all active agents"""
        try:
            docs = self.db.collection(self.collection_name).where(
                "status", "==", AgentStatus.ACTIVE.value
            ).stream()
            
            agents = []
            for doc in docs:
                agent_data = doc.to_dict()
                agents.append(AgentRegistryEntry(**agent_data))
            
            return agents
        except Exception as e:
            logger.error(f"Failed to get active agents list: {e}")
            return []
    
    async def get_agent_by_id(self, agent_id: str) -> Optional[AgentRegistryEntry]:
        """Get specific agent by ID"""
        try:
            doc = self.db.collection(self.collection_name).document(agent_id).get()
            
            if doc.exists:
                return AgentRegistryEntry(**doc.to_dict())
            return None
        except Exception as e:
            logger.error(f"Failed to get agent {agent_id}: {e}")
            return None
    
    async def create_agent_entry(self, agent: AgentRegistryEntry) -> bool:
        """Create new agent registry entry"""
        try:
            agent_dict = agent.model_dump()
            agent_dict["updated_at"] = datetime.now().timestamp()
            
            self.db.collection(self.collection_name).document(agent.agent_id).set(agent_dict)
            logger.info(f"Successfully created agent: {agent.agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            return False
    
    async def update_agent_status(self, agent_id: str, status: AgentStatus, error_message: Optional[str] = None) -> bool:
        """Update agent status"""
        try:
            update_data = {
                "status": status.value,
                "updated_at": datetime.now().timestamp()
            }
            
            if error_message:
                update_data["metadata.error_message"] = error_message
            
            self.db.collection(self.collection_name).document(agent_id).update(update_data)
            logger.info(f"Updated agent {agent_id} status to: {status.value}")
            return True
        except Exception as e:
            logger.error(f"Failed to update agent status: {e}")
            return False
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete agent (except system agents)"""
        # Check if this is a system agent
        is_system = await self.initialization_service.is_system_agent(agent_id)
        if is_system:
            logger.warning(f"Cannot delete system agent: {agent_id}")
            return False
        
        try:
            self.db.collection(self.collection_name).document(agent_id).delete()
            logger.info(f"Successfully deleted agent: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete agent: {e}")
            return False
    
    async def find_agents_by_capability(self, capability: str) -> List[AgentRegistryEntry]:
        """Find agents by capability tags"""
        try:
            docs = self.db.collection(self.collection_name).where(
                "capabilities", "array_contains", capability
            ).where("status", "==", AgentStatus.ACTIVE.value).stream()
            
            agents = []
            for doc in docs:
                agent_data = doc.to_dict()
                agents.append(AgentRegistryEntry(**agent_data))
            
            return agents
        except Exception as e:
            logger.error(f"Failed to find agents by capability: {e}")
            return []
    
    async def create_agent(self, request) -> str:
        """Create new agent"""
        # Implementation for creating new agents
        # This would integrate with the agent deployment service
        pass
    
    async def update_agent(self, agent_id: str, updates: dict) -> bool:
        """Update agent information (except system agents)"""
        # Check if this is a system agent
        is_system = await self.initialization_service.is_system_agent(agent_id)
        if is_system:
            logger.warning(f"Cannot update system agent: {agent_id}")
            return False
        
        try:
            updates["updated_at"] = datetime.now().timestamp()
            self.db.collection(self.collection_name).document(agent_id).update(updates)
            logger.info(f"Successfully updated agent: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update agent: {e}")
            return False
    
    def get_agents_summary_for_orchestrator(self) -> str:
        """Provide agent capability summary for OrchestratorAgent"""
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            agents = loop.run_until_complete(self.get_active_agents())
            
            if not agents:
                return "No expert agents currently available."
            
            summary_parts = ["Currently available expert agents:"]
            
            for agent in agents:
                if agent.agent_id != "orchestrator-agent":  # Exclude self
                    capabilities_str = ", ".join(agent.capabilities) if agent.capabilities else "general"
                    summary_parts.append(
                        f"- {agent.name} ({agent.agent_id}): {agent.description}\n"
                        f"  Capabilities: {capabilities_str}"
                    )
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Failed to get agents summary: {e}")
            return "Unable to get agent information."

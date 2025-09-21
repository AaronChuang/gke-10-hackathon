import os
import logging

from app.shared_crew_lib.clients import gcp_clients
from app.shared_crew_lib.schemas.agent_registry import AgentRegistryEntry, PromptStructure, AgentStatus

logger = logging.getLogger(__name__)

class AgentInitializationService:
    """Agent Initialization Service - Handles default agent setup on service startup"""
    
    def __init__(self):
        self.db = None
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self._initialize_db_client()
    
    def _initialize_db_client(self):
        try:
            self.db = gcp_clients.get_firestore_client()
            if self.db is None:
                raise RuntimeError("Failed to initialize Firestore client")
            logger.info("Firestore client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            raise
    
    async def initialize_default_agents(self):
        """Initialize default agents (OrchestratorAgent and ProxyAgent) if they don't exist"""
        try:
            # Ensure agents collection exists
            await self._ensure_agents_collection()
            
            # Initialize default agents
            await self._initialize_orchestrator_agent()
            await self._initialize_proxy_agent()
            
            logger.info("Default agents initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize default agents: {e}")
            raise
    
    async def _ensure_agents_collection(self):
        """Ensure the agents collection exists"""
        try:
            # Try to get the collection - this will create it if it doesn't exist
            agents_ref = self.db.collection("agents")
            
            # Check if collection exists by trying to get a document
            docs = list(agents_ref.limit(1).stream())
            logger.info("Agents collection verified/created")
            
        except Exception as e:
            logger.error(f"Failed to ensure agents collection: {e}")
            raise
    
    async def _initialize_orchestrator_agent(self):
        """Initialize OrchestratorAgent if it doesn't exist"""
        agent_id = "orchestrator-agent"
        
        try:
            # Check if agent already exists
            agent_doc = self.db.collection("agents").document(agent_id).get()
            
            if agent_doc.exists:
                logger.info(f"OrchestratorAgent already exists: {agent_id}")
                return
            
            # Create OrchestratorAgent entry
            orchestrator_prompt = PromptStructure(
                task_context="You are an Intelligent Task Coordinator and Agent Manager responsible for analyzing user intent and routing tasks to appropriate agents.",
                tone_context="Professional, helpful, and efficient. Always provide clear explanations of your decisions.",
                background_data_placeholder="[[AVAILABLE_AGENTS]]",
                rules=[
                    "Analyze user queries to determine the most appropriate action",
                    "Route tasks to specialized agents when needed",
                    "Handle agent management operations (create, update, delete, query)",
                    "Provide direct responses for simple queries",
                    "Never delete or modify system agents (orchestrator-agent, proxy-agent)"
                ],
                examples="User: 'Create a new tech analyst agent' -> Route to agent creation workflow\nUser: 'Hello' -> Provide direct greeting response",
                output_formatting="Always respond with structured JSON containing status, message, and appropriate action fields.",
                thinking_step="First analyze the user's intent, then determine the best course of action."
            )
            
            orchestrator_entry = AgentRegistryEntry(
                agent_id=agent_id,
                name="Orchestrator Agent",
                description="Intelligent task coordinator responsible for intent recognition, task routing, and agent lifecycle management",
                prompt_structure=orchestrator_prompt,
                status=AgentStatus.ACTIVE,
                pubsub_topic=f"{agent_id}-topic",
                capabilities=[
                    "intent_analysis",
                    "task_routing", 
                    "agent_management",
                    "system_coordination"
                ],
                metadata={
                    "is_system_agent": True,
                    "deletable": False,
                    "can_be_called_by": ["proxy-agent"],
                    "can_call": ["all"]
                }
            )
            
            # Save to database
            self.db.collection("agents").document(agent_id).set(orchestrator_entry.dict())
            logger.info(f"Created OrchestratorAgent: {agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize OrchestratorAgent: {e}")
            raise
    
    async def _initialize_proxy_agent(self):
        """Initialize ProxyAgent if it doesn't exist"""
        agent_id = "proxy-agent"
        
        try:
            # Check if agent already exists
            agent_doc = self.db.collection("agents").document(agent_id).get()
            
            if agent_doc.exists:
                logger.info(f"ProxyAgent already exists: {agent_id}")
                return
            
            # Create ProxyAgent entry
            proxy_prompt = PromptStructure(
                task_context="You are a General Task Proxy Agent that handles general queries and can forward complex requests to specialized agents.",
                tone_context="Friendly, helpful, and conversational. Always try to assist users directly when possible.",
                background_data_placeholder="[[CONVERSATION_HISTORY]]",
                rules=[
                    "Handle general user queries and provide helpful responses",
                    "Forward complex or specialized tasks to appropriate agents",
                    "Maintain conversation context and provide personalized assistance",
                    "Always prioritize user satisfaction and clear communication"
                ],
                examples="User: 'What's the weather like?' -> Provide general response about checking weather services\nUser: 'Analyze this technical architecture' -> Forward to technical specialist",
                output_formatting="Respond naturally in conversation format, or with structured JSON when forwarding tasks.",
                thinking_step="Consider if this is a general query I can handle directly, or if it needs specialized expertise."
            )
            
            proxy_entry = AgentRegistryEntry(
                agent_id=agent_id,
                name="Proxy Agent",
                description="General conversation agent that handles basic queries and forwards complex requests to specialized agents",
                prompt_structure=proxy_prompt,
                status=AgentStatus.ACTIVE,
                pubsub_topic=f"{agent_id}-topic",
                capabilities=[
                    "general_conversation",
                    "task_forwarding",
                    "user_assistance",
                    "context_management"
                ],
                metadata={
                    "is_system_agent": True,
                    "deletable": False,
                    "can_be_called_by": [],  # No other agents can call ProxyAgent
                    "can_call": ["all"]  # ProxyAgent can call all other agents
                }
            )
            
            # Save to database
            self.db.collection("agents").document(agent_id).set(proxy_entry.dict())
            logger.info(f"Created ProxyAgent: {agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ProxyAgent: {e}")
            raise
    
    async def is_system_agent(self, agent_id: str) -> bool:
        """Check if an agent is a system agent (non-deletable)"""
        try:
            agent_doc = self.db.collection("agents").document(agent_id).get()
            if agent_doc.exists:
                agent_data = agent_doc.to_dict()
                return agent_data.get("metadata", {}).get("is_system_agent", False)
            return False
        except Exception as e:
            logger.error(f"Failed to check if agent is system agent: {e}")
            return False
    
    async def can_agent_call(self, caller_agent_id: str, target_agent_id: str) -> bool:
        """Check if caller agent can call target agent"""
        try:
            target_doc = self.db.collection("agents").document(target_agent_id).get()
            if not target_doc.exists:
                return False
            
            target_data = target_doc.to_dict()
            can_be_called_by = target_data.get("metadata", {}).get("can_be_called_by", [])
            
            # If empty list or contains "all", anyone can call
            if not can_be_called_by or "all" in can_be_called_by:
                return True
            
            # Check if caller is in the allowed list
            return caller_agent_id in can_be_called_by
            
        except Exception as e:
            logger.error(f"Failed to check agent call permissions: {e}")
            return False

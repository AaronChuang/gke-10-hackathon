from crewai import Agent, Task
from typing import Dict, Any, Optional
from enum import Enum

from langchain_google_vertexai import ChatVertexAI

from .base import BaseAgentWrapper
from app.shared_crew_lib.schemas.agent_output import AgentResponse
from app.shared_crew_lib.services.agent_deployment_service import AgentDeploymentService, AgentInfo
from app.shared_crew_lib.services.agent_communication_service import AgentCommunicationService
from app.shared_crew_lib.services.agent_initialization_service import AgentInitializationService
import logging

logger = logging.getLogger(__name__)

class IntentType(Enum):
    """Intent type enumeration"""
    SIMPLE_GREETING = "SIMPLE_GREETING"
    PRODUCT_INQUIRY = "PRODUCT_INQUIRY"
    STYLE_ADVICE = "STYLE_ADVICE"
    TECHNICAL_ANALYSIS = "TECHNICAL_ANALYSIS"
    AGENT_MANAGEMENT = "AGENT_MANAGEMENT"
    AGENT_CREATION = "AGENT_CREATION"
    AGENT_DELETION = "AGENT_DELETION"
    AGENT_QUERY = "AGENT_QUERY"
    TASK_FORWARDING = "TASK_FORWARDING"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class OrchestratorAgent(BaseAgentWrapper):
    """Orchestrator Agent - Responsible for intent recognition and task routing"""
    
    def __init__(self, task_id: str = None):
        super().__init__("orchestrator-agent", task_id)
        self.deployment_service = AgentDeploymentService()
        self.communication_service = AgentCommunicationService()
        self.initialization_service = AgentInitializationService()

    
    async def initialize_system(self):
        """Initialize system agents on startup"""
        try:
            await self.initialization_service.initialize_default_agents()
            logger.info("System initialization completed successfully")
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            raise

    def get_llm(self, project_id) -> ChatVertexAI:
        return ChatVertexAI(
            project=project_id,
            model_name="gemini-2.5-flash-lite",
            temperature=0.7,
            max_output_tokens=4096,
            top_p=0.95,
            top_k=40,
            convert_system_message_to_human=True
        )

    def create_agent(self) -> Agent:
        """Create orchestrator agent instance"""
        # Use base class structured prompt assembly method
        system_prompt = self._assemble_prompt_context()
        
        return Agent(
            role="Intelligent Task Coordinator and Agent Manager",
            goal="Accurately identify user intent, intelligently route tasks, and manage agent lifecycle",
            backstory=system_prompt,
            llm=self.llm,
            allow_delegation=False,
            verbose=True
        )
    
    def create_task(self, input_data: Dict[str, Any]) -> Task:
        """Create intent analysis task with structured output"""
        user_prompt = input_data.get('user_prompt', '')
        conversation_history = input_data.get('conversation_history', [])
        product_context = input_data.get('product_context', {})
        
        # Build context
        context_parts = [f"User input: {user_prompt}"]
        
        if conversation_history:
            context_parts.append("\nConversation history:")
            for msg in conversation_history[-3:]:
                sender = "User" if msg.get("sender") == "user" else "AI"
                context_parts.append(f"{sender}: {msg.get('text', '')}")
        
        if product_context:
            context_parts.append(f"\nCurrent product: {product_context.get('name', '')} - {product_context.get('description', '')}")
        
        context = "\n".join(context_parts)
        
        return Task(
            description=f"""
            Analyze the following user input and decide the appropriate action:

            {context}

            Analyze user intent and decide whether to forward to other agents.
            Possible intents include:
            1. SIMPLE_GREETING - Simple greetings, thanks, or casual chat
            2. PRODUCT_INQUIRY - Basic product information queries
            3. STYLE_ADVICE - Styling and fashion advice requests (forward to stylist-agent)
            4. TECHNICAL_ANALYSIS - AI technical and architecture analysis requests (forward to tech-analyst-agent)
            5. AGENT_MANAGEMENT - Agent management requests (I can handle directly)
            6. OUT_OF_SCOPE - Requests outside business scope
            """,
            expected_output="Structured response with action decision and content",
            output_pydantic=AgentResponse,
            agent=self.agent
        )
    
    async def handle_agent_management(self, intent: IntentType, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent management requests"""
        user_prompt = input_data.get('user_prompt', '')
        
        try:
            if intent == IntentType.AGENT_CREATION:
                return await self._handle_agent_creation(user_prompt, input_data)
            elif intent == IntentType.AGENT_DELETION:
                return await self._handle_agent_deletion(user_prompt)
            elif intent == IntentType.AGENT_QUERY:
                return await self._handle_agent_query()
            else:
                return {"status": "ERROR", "message": "Unknown agent management request"}
                
        except Exception as e:
            logger.error(f"Failed to handle agent management request: {e}")
            return {"status": "ERROR", "message": f"Processing failed: {str(e)}"}
    
    async def _handle_agent_creation(self, user_prompt: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent creation requests"""
        # Analyze user requirements and generate agent specification
        agent_spec = self._analyze_agent_requirements(user_prompt)
        
        return {
            "status": "PLANNING",
            "message": "Agent creation plan generated, please confirm before execution",
            "agent_spec": agent_spec,
            "confirmation_required": True
        }
    
    async def _handle_agent_deletion(self, user_prompt: str) -> Dict[str, Any]:
        """Handle agent deletion requests"""
        # Extract agent ID to delete from user input
        agent_id = self._extract_agent_id_from_prompt(user_prompt)
        
        if not agent_id:
            available_agents = await self.communication_service.get_available_agents()
            return {
                "status": "INFO",
                "message": "Please specify the agent ID to delete",
                "available_agents": available_agents
            }
        
        return {
            "status": "CONFIRMATION_REQUIRED",
            "message": f"Confirm deletion of agent {agent_id}? This will remove all related resources.",
            "agent_id": agent_id,
            "action": "delete_agent"
        }
    
    async def _handle_agent_query(self) -> Dict[str, Any]:
        """Handle agent query requests"""
        available_agents = await self.communication_service.get_available_agents()
        
        return {
            "status": "SUCCESS",
            "message": "Current available agents list",
            "agents": available_agents
        }
    
    async def execute_agent_creation(self, agent_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent creation (after user confirmation)"""
        try:
            # Create AgentInfo object
            agent_info = AgentInfo(
                agent_id=agent_spec["agent_id"],
                agent_type=agent_spec["agent_type"],
                role=agent_spec["role"],
                goal=agent_spec["goal"],
                backstory=agent_spec["backstory"],
                capabilities=agent_spec.get("capabilities", []),
                status="CREATING"
            )
            
            # Save to database
            await self._save_agent_to_database(agent_info)
            
            # Create resources
            result = await self.deployment_service.create_agent_resources(agent_info)
            
            if result["status"] == "SUCCESS":
                # Broadcast new agent registration
                await self.communication_service.broadcast_agent_registry_update(
                    "AGENT_ADDED", agent_info.dict()
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute agent creation: {e}")
            return {"status": "ERROR", "error": str(e)}
    
    async def execute_agent_deletion(self, agent_id: str) -> Dict[str, Any]:
        """Execute agent deletion (after user confirmation)"""
        try:
            result = await self.deployment_service.delete_agent_resources(agent_id)
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute agent deletion: {e}")
            return {"status": "ERROR", "error": str(e)}
    
    async def forward_task_to_suitable_agent(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Forward task to suitable agent"""
        try:
            task_description = task_data.get("user_prompt", "")
            required_capabilities = task_data.get("required_capabilities", [])
            
            # Find suitable agent
            suitable_agent = await self.communication_service.find_suitable_agent(
                task_description, required_capabilities
            )
            
            if not suitable_agent:
                return {
                    "status": "ERROR",
                    "message": "No suitable agent found to handle this task"
                }
            
            # Forward task
            result = await self.communication_service.forward_task_to_agent(
                suitable_agent["agent_id"], task_data, "orchestrator-agent"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Task forwarding failed: {e}")
            return {"status": "ERROR", "error": str(e)}
    
    def _analyze_agent_requirements(self, user_prompt: str) -> Dict[str, Any]:
        """Analyze user requirements and generate agent specification"""
        # Generate agent specification based on user input
        prompt_lower = user_prompt.lower()
        
        # Default specification
        import time
        agent_spec = {
            "agent_id": f"custom-agent-{int(time.time())}",
            "agent_type": "omni_agent",
            "role": "General Assistant",
            "goal": "Assist users with various tasks",
            "backstory": "You are a flexible AI assistant capable of adapting to various task requirements.",
            "capabilities": ["general_assistance"]
        }
        
        # Adjust specification based on keywords
        if any(keyword in prompt_lower for keyword in ["technical", "tech", "programming", "development", "architecture"]):
            agent_spec.update({
                "agent_id": f"tech-specialist-{int(time.time())}",
                "role": "Technical Expert",
                "goal": "Provide technical analysis and development advice",
                "backstory": "You are an experienced technical expert specializing in software development and system architecture.",
                "capabilities": ["technical_analysis", "code_review", "architecture_design"]
            })
        elif any(keyword in prompt_lower for keyword in ["design", "aesthetic", "style", "ui", "fashion"]):
            agent_spec.update({
                "agent_id": f"design-specialist-{int(time.time())}",
                "role": "Design Expert",
                "goal": "Provide design advice and aesthetic guidance",
                "backstory": "You are a creative design expert skilled in UI/UX design and visual aesthetics.",
                "capabilities": ["ui_design", "visual_design", "user_experience"]
            })
        
        return agent_spec
    
    def _extract_agent_id_from_prompt(self, user_prompt: str) -> Optional[str]:
        """Extract agent ID from user input"""
        # Simple regex matching, may need more complex NLP in production
        import re
        
        # Look for patterns like "agent-id" or "agent ID"
        patterns = [
            r'([a-zA-Z0-9-]+(?:agent|specialist)[a-zA-Z0-9-]*)',
            r'ID[：:]\s*([a-zA-Z0-9-]+)',
            r'agent[：:]\s*([a-zA-Z0-9-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_prompt, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    async def _save_agent_to_database(self, agent_info: AgentInfo):
        """Save agent information to database"""
        from google.cloud import firestore
        
        agent_data = agent_info.dict()
        agent_data["created_at"] = firestore.SERVER_TIMESTAMP
        agent_data["updated_at"] = firestore.SERVER_TIMESTAMP
        
        self.db.collection("agents").document(agent_info.agent_id).set(agent_data)
    

from crewai import Agent, Task
from typing import Dict, Any

from langchain_google_vertexai import ChatVertexAI

from .base import BaseAgentWrapper
from app.shared_crew_lib.schemas.agent_output import AgentResponse


class OmniAgent(BaseAgentWrapper):
    """Omni Agent - Configurable universal agent with customizable role and goals"""
    
    def __init__(self, task_id: str = None,
                 custom_role: str = None, custom_goal: str = None, custom_backstory: str = None):
        self.custom_role = custom_role
        self.custom_goal = custom_goal
        self.custom_backstory = custom_backstory
        super().__init__("omni-agent", task_id)


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
        """Create configurable omni agent instance"""
        # If custom configuration exists, use custom backstory; otherwise use structured prompt
        if self.custom_backstory:
            backstory = self.custom_backstory
        else:
            # Use base class structured prompt assembly method
            backstory = self._assemble_prompt_context()
        
        role = self.custom_role or "Omni Intelligence Assistant"
        goal = self.custom_goal or "Provide professional and accurate assistance based on user needs"
        
        return Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            llm=self.llm,
            allow_delegation=False,
            verbose=True
        )
    
    def create_task(self, input_data: Dict[str, Any]) -> Task:
        """Create omni task with structured output"""
        user_prompt = input_data.get('user_prompt', '')
        conversation_history = input_data.get('conversation_history', [])
        product_context = input_data.get('product_context', {})
        custom_instructions = input_data.get('custom_instructions', '')
        
        # Build context
        context_parts = [f"User request: {user_prompt}"]
        
        if conversation_history:
            context_parts.append("\nConversation history:")
            for msg in conversation_history[-5:]:  # Keep more history for better context
                sender = "User" if msg.get("sender") == "user" else "AI"
                context_parts.append(f"{sender}: {msg.get('text', '')}")
        
        if product_context:
            context_parts.append(f"\nRelated product information: {product_context.get('name', '')} - {product_context.get('description', '')}")
        
        if custom_instructions:
            context_parts.append(f"\nSpecial instructions: {custom_instructions}")
        
        context = "\n".join(context_parts)
        
        return Task(
            description=f"""
            Analyze the following user request and decide the appropriate action:

            {context}

            Based on your role and capabilities, analyze user needs and decide whether to forward to other specialized agents.
            If the question is outside your expertise, consider forwarding to relevant experts.
            Otherwise, provide a direct professional response.
            """,
            expected_output="Structured response with action decision and content",
            output_pydantic=AgentResponse,
            agent=self.agent
        )
    
    def update_configuration(self, role: str = None, goal: str = None, backstory: str = None):
        """Dynamically update agent configuration"""
        if role:
            self.custom_role = role
        if goal:
            self.custom_goal = goal
        if backstory:
            self.custom_backstory = backstory
        
        # Recreate agent to apply new configuration
        self.agent = self.create_agent()
    
    def get_current_configuration(self) -> Dict[str, str]:
        """Get current configuration"""
        return {
            "role": self.custom_role or "Omni Intelligence Assistant",
            "goal": self.custom_goal or "Provide professional and accurate assistance based on user needs",
            "backstory": self.custom_backstory or "Default background story"
        }

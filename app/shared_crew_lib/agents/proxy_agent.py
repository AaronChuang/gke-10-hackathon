from crewai import Agent, Task
from typing import Dict, Any
import os

from langchain_google_vertexai import ChatVertexAI

from .base import BaseAgentWrapper
from app.shared_crew_lib.services.rag_service import RAGService
from app.shared_crew_lib.tools.rag_tool import RAGKnowledgeSearchTool
from app.shared_crew_lib.clients import gcp_clients


class ProxyAgent(BaseAgentWrapper):
    """Customer Service Agent - Handles general customer inquiries and forwards specialized requests"""
    
    def __init__(self, task_id: str = None):
        # Initialize RAG service
        project_id = os.getenv("GCP_PROJECT_ID")
        location = "us-central1"
        async_db = gcp_clients.get_async_firestore_client()
        self.rag_service = RAGService(project_id=project_id, location=location, db=async_db)
        
        super().__init__("proxy-agent", task_id)

    def get_llm(self, project_id) -> ChatVertexAI:
        return ChatVertexAI(
            project=project_id,
            model_name="gemini-2.5-flash-lite",
            temperature=0.2,
            max_output_tokens=4096,
            convert_system_message_to_human=True
        )

    def create_agent(self) -> Agent:
        """Create proxy agent instance with RAG tools"""
        system_prompt = self._assemble_prompt_context()

        # Create RAG tool for knowledge base access
        tools = []
        try:
            kb_id = os.getenv("RAG_KB_ID", "kb_35_236_185_81_1758459342")
            endpoint_name = os.getenv("RAG_ENDPOINT_NAME", f"{kb_id.replace('_', '-')}-endpoint")
            deployed_index_id = os.getenv("RAG_DEPLOYED_INDEX_ID", f"deployed_{kb_id}")
            
            rag_tool = RAGKnowledgeSearchTool(
                rag_service=self.rag_service,
                kb_id=kb_id,
                index_endpoint_name=endpoint_name,
                deployed_index_id=deployed_index_id
            )
            tools.append(rag_tool)
            print(f"Proxy Agent: Successfully initialized RAG tool with kb_id: {kb_id}")
        except Exception as e:
            print(f"Proxy Agent: Warning - Failed to initialize RAG tool: {e}")

        return Agent(
            role="Customer Service Agent for 'Online Boutique'",
            goal="Serve as the primary contact for 'Online Boutique' users. Try to use the Knowledge Base Search tool when possible, but if it fails, provide helpful responses based on general e-commerce knowledge. Always follow the decision-making process to answer, reject, or forward queries appropriately.",
            backstory=system_prompt,
            llm=self.llm,
            tools=tools,
            verbose=True,
            allow_delegation=False,
            max_iter=3,  # Reduce max iterations to prevent infinite loops
            max_execution_time=20  # Reduce execution time
        )

    def create_task(self, input_data: Dict[str, Any]) -> Task:
        """Create proxy task with a structured decision-making process"""
        user_prompt = input_data.get('user_prompt', '')
        conversation_history = input_data.get('conversation_history', [])
        product_context = input_data.get('product_context', {})

        context_parts = [f"User query: {user_prompt}"]
        if conversation_history:
            context_parts.append("\nConversation history:")
            for msg in conversation_history[-3:]:
                sender = "User" if msg.get("sender") == "user" else "AI"
                context_parts.append(f"{sender}: {msg.get('text', '')}")
        if product_context:
            context_parts.append(
                f"\nRelated product: {product_context.get('name', '')} - {product_context.get('description', '')}")
        context = "\n".join(context_parts)

        task_description = f"""
        Analyze the user's request based on the provided context and follow the strict decision-making process below. Your domain of expertise is ONLY the 'Online Boutique' e-commerce store. 
        When you need information, you MUST use the 'Knowledge Base Search' tool.

        --- CONTEXT ---
        {context}

        --- CRITICAL INSTRUCTIONS ---
        1. Your analysis MUST result in a valid JSON object.
        2. The "action" field MUST be one of "RESPOND", "FORWARD", or "REJECT".
        3. Your thought process MUST be captured inside the "thought" key of the JSON. Do NOT output your thoughts as plain text.

         --- DECISION-MAKING PROCESS (Follow these steps in order) ---
        1. **Relevance Check**: Is the query related to 'Online Boutique'? If NO, action MUST be "REJECT".
        2. **Information Retrieval**: If relevant, try to use the 'Knowledge Base Search' tool with a clear, concise query to find relevant information. If the tool fails or returns an error, proceed with general knowledge.
        3. **Specialist Check**: Based on the user's query and any retrieved information, does this request require a specialist (e.g., a multi-step styling plan)? If YES, action MUST be "FORWARD".
        4. **General Inquiry**: If you have sufficient information (from knowledge base or general knowledge) to answer the question and it's not for a specialist, action MUST be "RESPOND".
        5. **Tool Failure Handling**: If the Knowledge Base Search tool fails repeatedly, provide a helpful response based on general e-commerce knowledge and apologize for not being able to access specific product details.

        --- RESPONSE FORMAT & EXAMPLES ---

        Example 1: General E-commerce Question
        <result>{{
            "thought": "Step 1: User asks about sunglasses. Step 2: This is relevant to our store. Step 3: I used Knowledge Base Search to find information about sunglasses. Step 4: I have sufficient information to answer. Action is RESPOND.",
            "action": "RESPOND",
            "response_content": "Yes, we have a wide variety of sunglasses available in our 'Accessories' section!",
            "forward_to_agent": null
        }}</result>

        Example 2: Specialist Question (Forwarding)
        <result>{{
            "thought": "Step 1: User asks for personalized style advice. Step 2: This is relevant. Step 3: I searched the knowledge base for styling information. Step 4: This requires a specialist for personalized advice. Action is FORWARD to stylist-agent.",
            "action": "FORWARD",
            "response_content": "That's a great question! I'm forwarding you to our style specialist who can give you the best advice. They will get back to you shortly.",
            "forward_to_agent": "stylist-agent"
        }}</result>

        Example 3: Off-Topic Question (Rejection)
        <result>{{
            "thought": "Step 1: User asks a math question '1+2=?'. Step 2: This is NOT relevant to our store. Step 3: Action is REJECT.",
            "action": "REJECT",
            "response_content": "I'm sorry, but I can only assist with questions related to our Online Boutique store and products.",
            "forward_to_agent": null
        }}</result>

        Example 4: Tool Failure Handling
        <result>{{
            "thought": "Step 1: User asks about hairdryer settings. Step 2: This is relevant to our store. Step 3: I tried Knowledge Base Search but it failed. Step 4: I'll provide general information and apologize. Action is RESPOND.",
            "action": "RESPOND",
            "response_content": "I apologize, but I'm currently unable to access our detailed product database. For specific hairdryer settings and features, I recommend checking the product page directly or contacting our customer service team who can provide detailed specifications.",
            "forward_to_agent": null
        }}</result>

        --- FINAL AND ABSOLUTE INSTRUCTION ---
        Your entire response MUST start *directly* with the opening "<result>" tag and end with the closing "</result>" tag. There should be ABSOLUTELY NO text, explanation, or markdown formatting before or after these tags.
        """

        return Task(
            description=task_description,
            expected_output="A single valid JSON object enclosed in <result></result> tags. No other text or explanation.",
            agent=self.agent
        )
    

from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ConversationMessage(BaseModel):
    sender: str  # "user" or "ai"
    text: str

class ProductContext(BaseModel):
    name: str
    description: str

class ConversationRequest(BaseModel):
    user_id: str
    user_prompt: str
    conversation_history: List[ConversationMessage] = []
    product_context: Optional[ProductContext] = None

class ConversationResponse(BaseModel):
    task_id: str
    agent_response: str
    action: str  # "DIRECT_REPLY" or "DELEGATED"
    delegated_to: Optional[str] = None

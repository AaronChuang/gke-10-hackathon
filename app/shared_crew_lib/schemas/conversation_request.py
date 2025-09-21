from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ConversationMessage(BaseModel):
    sender: str
    text: str

class ProductContext(BaseModel):
    name: str
    description: str

class ConversationRequest(BaseModel):
    user_id: Optional[str] = None
    user_prompt: str
    session_id: Optional[str] = None
    conversation_history: List[ConversationMessage] = []
    product_context: Optional[ProductContext] = None

class ConversationResponse(BaseModel):
    task_id: str
    agent_response: str
    action: str
    delegated_to: Optional[str] = None
    session_id: Optional[str] = None

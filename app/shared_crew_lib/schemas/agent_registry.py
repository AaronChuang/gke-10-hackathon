from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class AgentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    CREATING = "CREATING"
    FAILED = "FAILED"

class PromptStructure(BaseModel):
    """
    Structured prompt, aligned with best practices for prompt design.
    """
    task_context: str = Field(..., description="1. Task Context: Defines the agent's core role and objective.")
    tone_context: str = Field(...,
                              description="2. Tone Context: Describes the tone the agent should adopt in its responses.")
    background_data_placeholder: Optional[str] = Field(None,
                                                       description="3. Background Data Placeholder: Describes the type of dynamic RAG or background data to be injected, e.g., '[[DOCUMENT]]'.")
    rules: List[str] = Field(default_factory=list,
                             description="4. Detailed Task Description & Rules: Specific rules for this agent.")
    examples: Optional[str] = Field(None,
                                    description="5. Examples: Provides one or more few-shot examples to guide the model's response format.")
    output_formatting: str = Field(...,
                                   description="9. Output Formatting: Clearly defines the expected output format, such as a JSON Schema.")
    thinking_step: Optional[str] = Field(
        default="Think about your answer first before you respond.",
        description="8. Thinking Step Prompt: Guides the model to think step-by-step."
    )

class AgentRegistryEntry(BaseModel):
    """
    Enhanced agent registry entry.
    """
    agent_id: str = Field(..., description="Unique identifier for the agent.")
    name: str = Field(..., description="Display name of the agent.")
    description: str = Field(...,
                             description="A brief description of the agent's core responsibilities, used for inter-agent understanding.")

    # Use a structured prompt instead of a single system_prompt string
    prompt_structure: PromptStructure = Field(..., description="The structured prompt for the agent.")

    status: AgentStatus = Field(default=AgentStatus.ACTIVE, description="The status of the agent.")
    pubsub_topic: str = Field(..., description="The corresponding Pub/Sub topic.")
    version: str = Field(default="1.0.0", description="Version of the agent, especially for tracking prompt versions.")
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    capabilities: List[str] = Field(default_factory=list,
                                    description="Capability tags for the agent, used for task routing.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata.")

class CreateAgentRequest(BaseModel):
    """創建代理人請求"""
    name: str = Field(..., description="代理人名稱")
    description: str = Field(..., description="核心職責描述")

class CreateAgentResponse(BaseModel):
    """創建代理人回應 - OrchestratorAgent 生成的推薦提示"""
    agent_id: str
    name: str
    description: str
    recommended_system_prompt: str
    recommended_capabilities: List[str]

class FinalizeAgentRequest(BaseModel):
    """確認創建代理人請求"""
    agent_id: str
    name: str
    description: str
    system_prompt: str
    capabilities: List[str] = Field(default_factory=list)

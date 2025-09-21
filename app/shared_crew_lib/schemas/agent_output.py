from pydantic import BaseModel, Field, field_validator, ValidationInfo
from typing import Optional
from enum import Enum


class AgentAction(str, Enum):
    RESPOND = "RESPOND"
    FORWARD = "FORWARD"
    REJECT = "REJECT"


class ForwardInfo(BaseModel):
    agent_id: str = Field(..., description="ID of the target agent to forward the task to")
    reason: str = Field(..., description="Explanation of why the task needs to be forwarded")
    required_info: str = Field(..., description="All necessary information and context for the target agent")


class AgentResponse(BaseModel):
    """Standardized agent response model"""
    thought: str = Field(..., description="Step-by-step thinking process to analyze the problem")
    action: AgentAction = Field(..., description="The action to take")
    response_content: Optional[str] = Field(None, description="Final response content if action is RESPOND or REJECT")
    forward_to_agent: Optional[ForwardInfo] = Field(None, description="Forwarding information if action is FORWARD")

    @field_validator('action', mode='before')
    def normalize_action(cls, v):
        """Normalize action values to handle model inconsistencies"""
        if isinstance(v, str):
            v_lower = v.lower().strip()
            if v_lower in ['respond', 'respond_directly', 'response', 'answer']:
                return 'RESPOND'
            elif v_lower in ['forward', 'delegate', 'forward_to', 'send_to']:
                return 'FORWARD'
            elif v_lower in ['reject', 'decline']:
                return 'REJECT'
            elif v.upper() in ['RESPOND', 'FORWARD', 'REJECT']:
                return v.upper()
        return v

    @field_validator('response_content')
    def validate_response_content(cls, v, info: ValidationInfo):
        """Ensure response_content is provided when action is RESPOND or REJECT"""
        # 舊的錯誤寫法: if values.get('action') == 'RESPOND' and not v:
        # 正確的寫法:
        if info.data.get('action') in ['RESPOND', 'REJECT'] and not v:
            raise ValueError("response_content is required when action is RESPOND or REJECT")
        return v

    @field_validator('forward_to_agent')
    def validate_forward_to_agent(cls, v, info: ValidationInfo):
        """Ensure forward_to_agent is provided when action is FORWARD"""
        # 舊的錯誤寫法: if values.get('action') == 'FORWARD' and not v:
        # 正確的寫法:
        if info.data.get('action') == 'FORWARD' and not v:
            raise ValueError("forward_to_agent is required when action is FORWARD")
        return v

    class Config:
        use_enum_values = True
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class AgentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    CREATING = "CREATING"
    FAILED = "FAILED"

class AgentRegistryEntry(BaseModel):
    """代理人註冊表項目"""
    agent_id: str = Field(..., description="代理人唯一識別碼")
    name: str = Field(..., description="代理人顯示名稱")
    description: str = Field(..., description="代理人核心職責描述")
    system_prompt: str = Field(..., description="代理人系統提示")
    status: AgentStatus = Field(default=AgentStatus.ACTIVE, description="代理人狀態")
    pubsub_topic: str = Field(..., description="對應的 Pub/Sub 主題")
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    capabilities: List[str] = Field(default_factory=list, description="代理人能力標籤")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="額外元數據")

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

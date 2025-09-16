from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class Message(BaseModel):
    sender: str = Field(..., description="發送者 (user/agent)")
    text: str = Field(..., description="訊息內容")
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())

class ProductContext(BaseModel):
    product_name: Optional[str] = None
    product_description: Optional[str] = None
    product_category: Optional[str] = None
    product_price: Optional[float] = None
    product_url: Optional[str] = None

class AgentHistoryEntry(BaseModel):
    """代理人執行歷史記錄"""
    agent_id: str = Field(..., description="代理人 ID")
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    action: str = Field(..., description="執行動作")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TokenUsage(BaseModel):
    """Token 使用量統計"""
    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)

class TaskLogEntry(BaseModel):
    """任務執行日誌項目"""
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    event: str = Field(..., description="事件描述")
    agent_id: Optional[str] = Field(None, description="執行的代理人 ID")
    token_usage: Optional[TokenUsage] = Field(None, description="該步驟的 Token 消耗")
    details: Dict[str, Any] = Field(default_factory=dict)

class FirestoreTask(BaseModel):
    task_id: str
    status: str = Field(default="PENDING")
    initial_request: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    
    # 對話式支援欄位
    user_id: Optional[str] = None
    conversation_history: List[Message] = Field(default_factory=list)
    product_context: Optional[ProductContext] = None
    
    # 新增護欄和監控欄位
    agent_history: List[AgentHistoryEntry] = Field(default_factory=list, description="代理人執行歷史")
    total_tokens: TokenUsage = Field(default_factory=TokenUsage, description="總 Token 消耗")
    log: List[TaskLogEntry] = Field(default_factory=list, description="詳細執行日誌")
    tech_analyst_output: Optional[str] = None
    architect_output: Optional[str] = None
    stylist_output: Optional[str] = None
    error_source: Optional[str] = None
    error_message: Optional[str] = None

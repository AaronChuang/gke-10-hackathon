from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class MessageSender(str, Enum):
    """訊息發送者類型"""
    USER = "user"
    AI = "ai"
    SYSTEM = "system"

class ConversationMessage(BaseModel):
    """對話訊息"""
    message_id: str = Field(..., description="訊息唯一 ID")
    sender: MessageSender = Field(..., description="發送者類型")
    content: str = Field(..., description="訊息內容")
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    metadata: Dict[str, Any] = Field(default_factory=dict, description="額外的訊息元數據")

class ConversationStatus(str, Enum):
    """對話狀態"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class ConversationContext(BaseModel):
    """對話上下文"""
    user_id: Optional[str] = None
    session_type: str = Field(default="general", description="對話類型")
    language: str = Field(default="zh-TW", description="對話語言")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="使用者偏好設定")
    product_context: Optional[Dict[str, Any]] = Field(None, description="產品相關上下文")

class ConversationSummary(BaseModel):
    """對話摘要"""
    total_messages: int = Field(default=0)
    user_messages: int = Field(default=0)
    ai_messages: int = Field(default=0)
    topics: List[str] = Field(default_factory=list, description="對話主題")
    key_points: List[str] = Field(default_factory=list, description="重點摘要")
    sentiment: Optional[str] = Field(None, description="整體情感傾向")

class ConversationSession(BaseModel):
    """對話 Session 主要資料結構"""
    session_id: str = Field(..., description="Session ID (使用 Firestore document ID)")
    status: ConversationStatus = Field(default=ConversationStatus.ACTIVE)
    context: ConversationContext = Field(default_factory=ConversationContext)
    
    # 對話記錄
    messages: List[ConversationMessage] = Field(default_factory=list)
    
    # 時間戳記
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    last_activity_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    
    # 統計和摘要
    summary: ConversationSummary = Field(default_factory=ConversationSummary)
    
    # 關聯的任務 (如果有的話)
    related_tasks: List[str] = Field(default_factory=list, description="關聯的 Task IDs")
    
    # 元數據
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def add_message(self, sender: MessageSender, content: str, message_id: str = None, metadata: Dict[str, Any] = None) -> ConversationMessage:
        """添加新訊息到對話中"""
        import uuid
        if not message_id:
            message_id = str(uuid.uuid4())
            
        message = ConversationMessage(
            message_id=message_id,
            sender=sender,
            content=content,
            metadata=metadata or {}
        )
        
        self.messages.append(message)
        self.updated_at = datetime.now().timestamp()
        self.last_activity_at = datetime.now().timestamp()
        
        # 更新統計
        self.summary.total_messages += 1
        if sender == MessageSender.USER:
            self.summary.user_messages += 1
        elif sender == MessageSender.AI:
            self.summary.ai_messages += 1
            
        return message
    
    def get_recent_messages(self, limit: int = 10) -> List[ConversationMessage]:
        """獲取最近的訊息"""
        return self.messages[-limit:] if self.messages else []
    
    def get_conversation_history_for_ai(self, limit: int = 5) -> List[Dict[str, str]]:
        """獲取適合 AI 處理的對話歷史格式"""
        recent_messages = self.get_recent_messages(limit)
        return [
            {
                "sender": msg.sender.value,
                "text": msg.content,
                "timestamp": msg.timestamp
            }
            for msg in recent_messages
        ]

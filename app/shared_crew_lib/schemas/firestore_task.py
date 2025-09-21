from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class TaskType(str, Enum):
    """任務類型"""
    ANALYSIS = "analysis"           # 分析任務
    RESEARCH = "research"          # 研究任務
    GENERATION = "generation"      # 生成任務
    PROCESSING = "processing"      # 處理任務
    FORWARDING = "forwarding"      # 轉發任務
    WORKFLOW = "workflow"          # 工作流任務

class TaskPriority(str, Enum):
    """任務優先級"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskStatus(str, Enum):
    """任務狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

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
    total_tokens: int = Field(default=0)
    price: float = Field(default=0)

class TaskLogEntry(BaseModel):
    """任務執行日誌項目"""
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    event: str = Field(..., description="事件描述")
    agent_id: Optional[str] = Field(None, description="執行的代理人 ID")
    token_usage: Optional[TokenUsage] = Field(None, description="該步驟的 Token 消耗")
    details: Dict[str, Any] = Field(default_factory=dict)

class FirestoreTask(BaseModel):
    """非同步任務資料結構 - 專注於 AI 代理人的後台任務處理"""
    task_id: str = Field(..., description="任務唯一 ID")
    task_type: TaskType = Field(..., description="任務類型")
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    
    # 任務基本資訊
    title: str = Field(..., description="任務標題")
    description: Optional[str] = Field(None, description="任務描述")
    
    # 任務輸入和輸出
    input_data: Dict[str, Any] = Field(default_factory=dict, description="任務輸入資料")
    result: Optional[Dict[str, Any]] = Field(None, description="任務執行結果")
    error: Optional[str] = Field(None, description="錯誤訊息")
    
    # 執行相關
    assigned_agent: Optional[str] = Field(None, description="負責執行的代理人")
    parent_task_id: Optional[str] = Field(None, description="父任務 ID (用於子任務)")
    child_task_ids: List[str] = Field(default_factory=list, description="子任務 IDs")
    
    # 關聯資訊
    conversation_session_id: Optional[str] = Field(None, description="關聯的對話 Session ID")
    user_id: Optional[str] = Field(None, description="發起任務的使用者 ID")
    
    # 時間戳記
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    started_at: Optional[float] = Field(None, description="任務開始執行時間")
    completed_at: Optional[float] = Field(None, description="任務完成時間")
    
    # 執行統計
    agent_history: List[AgentHistoryEntry] = Field(default_factory=list, description="代理人執行歷史")
    total_tokens: TokenUsage = Field(default_factory=TokenUsage, description="總 Token 消耗")
    log: List[TaskLogEntry] = Field(default_factory=list, description="詳細執行日誌")
    
    # 任務特定輸出 (向後兼容)
    tech_analyst_output: Optional[str] = None
    architect_output: Optional[str] = None
    stylist_output: Optional[str] = None
    
    # 元數據
    metadata: Dict[str, Any] = Field(default_factory=dict, description="任務元數據")
    
    def mark_as_started(self):
        """標記任務為開始執行"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now().timestamp()
        self.updated_at = datetime.now().timestamp()
    
    def mark_as_completed(self, result: Dict[str, Any] = None):
        """標記任務為完成"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now().timestamp()
        self.updated_at = datetime.now().timestamp()
        if result:
            self.result = result
    
    def mark_as_failed(self, error: str):
        """標記任務為失敗"""
        self.status = TaskStatus.FAILED
        self.error = error
        self.updated_at = datetime.now().timestamp()

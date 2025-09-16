from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class KnowledgeBaseStatus(str, Enum):
    QUEUED = "QUEUED"
    CRAWLING = "CRAWLING"
    INDEXING = "INDEXING"
    ACTIVE = "ACTIVE"
    FAILED = "FAILED"

class KnowledgeBaseEntry(BaseModel):
    """知識庫項目"""
    kb_id: str = Field(..., description="知識庫唯一識別碼")
    url: str = Field(..., description="網站 URL")
    status: KnowledgeBaseStatus = Field(default=KnowledgeBaseStatus.QUEUED)
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    indexed_pages: int = Field(default=0, description="已索引頁面數")
    total_pages: int = Field(default=0, description="總頁面數")
    error_message: Optional[str] = Field(None, description="錯誤訊息")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class IndexWebsiteRequest(BaseModel):
    """索引網站請求"""
    url: str = Field(..., description="要索引的網站 URL")

class RAGQueryRequest(BaseModel):
    """RAG 查詢請求"""
    query: str = Field(..., description="查詢文本")
    top_k: int = Field(default=5, description="返回最相關的 K 個結果")
    similarity_threshold: float = Field(default=0.7, description="相似度閾值")

class RAGQueryResult(BaseModel):
    """RAG 查詢結果"""
    content: str = Field(..., description="相關內容片段")
    source_url: str = Field(..., description="來源 URL")
    similarity_score: float = Field(..., description="相似度分數")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RAGQueryResponse(BaseModel):
    """RAG 查詢回應"""
    results: List[RAGQueryResult] = Field(default_factory=list)
    total_results: int = Field(default=0)
    query_time_ms: float = Field(default=0.0)

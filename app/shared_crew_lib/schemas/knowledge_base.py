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
    """Represents a single entry in the knowledge base."""
    kb_id: str = Field(..., description="Unique identifier for the knowledge base.")
    url: str = Field(..., description="The URL of the website.")
    status: KnowledgeBaseStatus = Field(default=KnowledgeBaseStatus.QUEUED)
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    indexed_pages: int = Field(default=0, description="Number of pages indexed.")
    total_pages: int = Field(default=0, description="Total number of pages found.")
    error_message: Optional[str] = Field(None, description="Error message if indexing failed.")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class IndexWebsiteRequest(BaseModel):
    """Request to index a website."""
    url: str = Field(..., description="The URL of the website to index.")

class RAGQueryRequest(BaseModel):
    """Request for a RAG query."""
    query: str = Field(..., description="The query text.")
    top_k: int = Field(default=5, description="The number of top K results to return.")
    similarity_threshold: float = Field(default=0.7, description="The similarity threshold.")

class RAGQueryResult(BaseModel):
    """A single result from a RAG query."""
    content: str = Field(..., description="The relevant content snippet.")
    source_url: str = Field(..., description="The source URL of the content.")
    similarity_score: float = Field(..., description="The similarity score.")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RAGQueryResponse(BaseModel):
    """The response from a RAG query."""
    results: List[RAGQueryResult] = Field(default_factory=list)
    total_results: int = Field(default=0)
    query_time_ms: float = Field(default=0.0)

from typing import List, Optional, Dict, Any
import logging
from google.cloud import aiplatform
from google.cloud.aiplatform import MatchingEngineIndexEndpoint
from ..schemas.knowledge_base import RAGQueryRequest, RAGQueryResponse, RAGQueryResult
import time

logger = logging.getLogger(__name__)

class RAGService:
    """RAG (檢索增強生成) 服務 - 整合 Vertex AI Vector Search"""
    
    def __init__(self, project_id: str, location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
        self.client = None
        self.index_endpoint = None
        
    async def initialize(self, index_endpoint_id: Optional[str] = None):
        """初始化 Vertex AI Vector Search 客戶端"""
        try:
            aiplatform.init(project=self.project_id, location=self.location)
            
            if index_endpoint_id:
                self.index_endpoint = MatchingEngineIndexEndpoint(index_endpoint_id)
                logger.info(f"已連接到 Vector Search Index Endpoint: {index_endpoint_id}")
            else:
                logger.warning("未提供 index_endpoint_id，RAG 查詢將無法使用")
                
        except Exception as e:
            logger.error(f"初始化 RAG 服務失敗: {e}")
            raise
    
    async def query_knowledge_base(self, request: RAGQueryRequest) -> RAGQueryResponse:
        """查詢知識庫，返回最相關的內容片段"""
        start_time = time.time()
        
        if not self.index_endpoint:
            logger.warning("Vector Search Index Endpoint 未初始化")
            return RAGQueryResponse(
                results=[],
                total_results=0,
                query_time_ms=(time.time() - start_time) * 1000
            )
        
        try:
            # 生成查詢向量 (這裡需要實際的嵌入模型)
            query_embedding = await self._generate_embedding(request.query)
            
            # 執行向量搜索
            response = self.index_endpoint.find_neighbors(
                deployed_index_id="deployed_index",  # 需要配置
                queries=[query_embedding],
                num_neighbors=request.top_k
            )
            
            results = []
            for neighbor in response[0]:
                if neighbor.distance >= request.similarity_threshold:
                    # 從 Firestore 或其他存儲中獲取完整內容
                    content_data = await self._fetch_content_by_id(neighbor.id)
                    
                    if content_data:
                        results.append(RAGQueryResult(
                            content=content_data.get("content", ""),
                            source_url=content_data.get("source_url", ""),
                            similarity_score=neighbor.distance,
                            metadata=content_data.get("metadata", {})
                        ))
            
            query_time = (time.time() - start_time) * 1000
            
            return RAGQueryResponse(
                results=results,
                total_results=len(results),
                query_time_ms=query_time
            )
            
        except Exception as e:
            logger.error(f"RAG 查詢失敗: {e}")
            return RAGQueryResponse(
                results=[],
                total_results=0,
                query_time_ms=(time.time() - start_time) * 1000
            )
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """生成文本嵌入向量"""
        # TODO: 實現實際的嵌入生成邏輯
        # 可以使用 Vertex AI Text Embeddings API
        # 或其他嵌入模型如 OpenAI embeddings
        
        # 暫時返回假數據
        import random
        return [random.random() for _ in range(768)]  # 假設 768 維向量
    
    async def _fetch_content_by_id(self, content_id: str) -> Optional[Dict[str, Any]]:
        """根據 ID 獲取完整內容數據"""
        # TODO: 從 Firestore 或其他存儲中獲取內容
        # 這裡需要實現實際的數據獲取邏輯
        
        return {
            "content": f"模擬內容片段 {content_id}",
            "source_url": "https://example.com",
            "metadata": {"id": content_id}
        }
    
    def get_context_for_prompt(self, query: str, max_context_length: int = 2000) -> str:
        """為 LLM 提示獲取相關上下文"""
        # 同步版本的查詢方法，用於 Agent 中
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            request = RAGQueryRequest(query=query, top_k=3)
            response = loop.run_until_complete(self.query_knowledge_base(request))
            
            if not response.results:
                return "沒有找到相關的上下文資訊。"
            
            context_parts = []
            current_length = 0
            
            for result in response.results:
                content = f"來源: {result.source_url}\n內容: {result.content}\n"
                if current_length + len(content) <= max_context_length:
                    context_parts.append(content)
                    current_length += len(content)
                else:
                    break
            
            return "\n---\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"獲取上下文失敗: {e}")
            return "無法獲取相關上下文資訊。"

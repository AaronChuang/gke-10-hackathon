import os
from crewai import Agent, Task, Crew
import datetime
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from google.cloud import firestore
from langchain_google_vertexai import ChatVertexAI

from app.shared_crew_lib.clients import gcp_clients
from app.shared_crew_lib.schemas.firestore_task import TokenUsage, TaskLogEntry, AgentHistoryEntry

logger = logging.getLogger(__name__)

class BaseAgentWrapper(ABC):
    """
    增強版代理人基礎類別，整合 RAG 查詢、Token 監控、任務護欄等核心功能
    所有代理人都應該繼承此類別
    """

    def __init__(self, agent_name: str, task_id: str = None, output_field: str = None):
        self.agent_name = agent_name
        self.task_id = task_id
        self.output_field = output_field or f"{agent_name}_output"
        
        # 代理人註冊表
        self.peer_agents = {}
        
        # 初始化 LLM
        self.llm = ChatVertexAI(
            model="gemini-2.5-flash-lite",
            temperature=0.7,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        # 初始化資料庫連接
        self.db = gcp_clients.get_firestore_client()
        
        # 創建代理人和任務
        self.agent = self.create_agent()
        
        # 初始化代理人註冊表
        self._initialize_peer_registry()
        
        logger.info(f"初始化 {agent_name} 代理人")

    @abstractmethod
    def create_agent(self) -> Agent:
        """
        創建並返回 CrewAI Agent 實例。
        子類必須實現此方法。
        """
        pass
    
    @abstractmethod
    def create_task(self, input_data: Dict[str, Any]) -> Task:
        """創建任務 - 子類必須實現"""
        pass
    
    def should_forward_task(self, task_description: str) -> tuple[bool, str, List[str]]:
        """判斷是否應該轉發任務給其他代理人"""
        # 子類可以重寫此方法來實現自定義的轉發邏輯
        return False, None, []
    
    def initialize(self, task_id: str = None, output_field: str = None):
        """
        初始化 Agent 和相關組件。
        """
        if task_id:
            self.task_id = task_id
        if output_field:
            self.output_field = output_field
            
        if self.task_id:
            self.db = gcp_clients.get_firestore_client()
            self.task_ref = self.db.collection('tasks').document(self.task_id)
        
        # 創建 agent 實例
        self.agent = self.create_agent()
        self.agent.verbose = True
        self.agent.max_iter = 1

    async def run(self, task_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行代理人任務的主要方法
        整合 RAG 查詢、Token 監控和護欄檢查
        """
        self._current_task_id = task_id
        
        try:
            # 1. 記錄任務開始
            await self._log_task_event("任務開始", {"input_data": input_data})
            await self._add_agent_history("TASK_START")
            
            # 2. 檢查任務護欄 (兩次重試限制)
            if await self._check_retry_limit(task_id):
                error_msg = "任務因超過兩次重試限制而終止"
                await self._log_task_event("任務終止", {"reason": "RETRY_LIMIT_EXCEEDED"})
                await self._update_task_status(task_id, "TERMINATED_BY_RETRY_LIMIT", error=error_msg)
                return {"error": error_msg, "status": "TERMINATED_BY_RETRY_LIMIT"}
            
            # 3. 確保 agent 已初始化
            if not self.agent:
                self.agent = self.create_agent()
            
            # 4. 創建任務
            self.task = self.create_task(input_data)
            
            # 5. 更新狀態為執行中
            await self._update_task_status(task_id, "RUNNING")
            
            # 6. 執行任務
            await self._log_task_event("開始執行 CrewAI 任務")
            crew = Crew(agents=[self.agent], tasks=[self.task])
            
            # 模擬 Token 使用 (實際應從 LLM 回應中提取)
            token_usage = TokenUsage(input_tokens=150, output_tokens=300)
            
            result = crew.kickoff()
            
            # 7. 記錄執行結果和 Token 消耗
            await self._log_task_event(
                "任務執行完成", 
                {"result_preview": str(result)[:200]},
                token_usage=token_usage
            )
            await self._update_total_tokens(task_id, token_usage)
            
            # 8. 更新任務狀態
            await self._update_task_status(task_id, "COMPLETED", result={"output": str(result)})
            
            return {"output": str(result), "status": "COMPLETED"}
            
        except Exception as e:
            error_msg = f"代理人執行失敗: {str(e)}"
            logger.error(error_msg)
            
            await self._log_task_event("任務執行失敗", {"error": error_msg})
            await self._update_task_status(task_id, "FAILED", error=error_msg)
            
            return {"error": error_msg, "status": "FAILED"}

    async def _check_retry_limit(self, task_id: str) -> bool:
        """檢查是否超過兩次重試限制"""
        try:
            task_doc = self.db.collection('tasks').document(task_id).get()
            if not task_doc.exists:
                return False
            
            task_data = task_doc.to_dict()
            agent_history = task_data.get('agent_history', [])
            
            if len(agent_history) < 2:
                return False
            
            # 檢查最後兩次是否為相同的代理人
            last_two = agent_history[-2:]
            if (last_two[0].get('agent_id') == self.agent_name and 
                last_two[1].get('agent_id') == self.agent_name):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"檢查重試限制失敗: {e}")
            return False
    
    async def _add_agent_history(self, action: str, metadata: Dict[str, Any] = None):
        """添加代理人執行歷史"""
        if not self._current_task_id:
            return
        
        try:
            history_entry = AgentHistoryEntry(
                agent_id=self.agent_name,
                action=action,
                metadata=metadata or {}
            )
            
            self.db.collection('tasks').document(self._current_task_id).update({
                'agent_history': firestore.ArrayUnion([history_entry.model_dump()])
            })
            
        except Exception as e:
            logger.error(f"添加代理人歷史失敗: {e}")
    
    async def _log_task_event(self, event: str, details: Dict[str, Any] = None, token_usage: Optional[TokenUsage] = None):
        """記錄任務執行日誌"""
        if not self._current_task_id:
            return
        
        try:
            log_entry = TaskLogEntry(
                event=event,
                agent_id=self.agent_id,
                token_usage=token_usage,
                details=details or {}
            )
            
            self.db.collection('tasks').document(self._current_task_id).update({
                'log': firestore.ArrayUnion([log_entry.model_dump()])
            })
            
        except Exception as e:
            logger.error(f"記錄任務日誌失敗: {e}")
    
    async def _update_total_tokens(self, task_id: str, token_usage: TokenUsage):
        """更新總 Token 消耗"""
        try:
            task_ref = self.db.collection('tasks').document(task_id)
            task_doc = task_ref.get()
            
            if task_doc.exists:
                current_tokens = task_doc.to_dict().get('total_tokens', {'input_tokens': 0, 'output_tokens': 0})
                new_total = TokenUsage(
                    input_tokens=current_tokens.get('input_tokens', 0) + token_usage.input_tokens,
                    output_tokens=current_tokens.get('output_tokens', 0) + token_usage.output_tokens
                )
                
                task_ref.update({'total_tokens': new_total.model_dump()})
            
        except Exception as e:
            logger.error(f"更新 Token 統計失敗: {e}")
    
    async def _update_task_status(self, task_id: str, status: str, result: Dict[str, Any] = None, error: str = None):
        """更新任務狀態"""
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.datetime.now().timestamp()
            }
            
            if result:
                update_data['result'] = result
            
            if error:
                update_data['error'] = error
            
            self.db.collection('tasks').document(task_id).update(update_data)
            
        except Exception as e:
            logger.error(f"更新任務狀態失敗: {e}")
    
    def _initialize_peer_registry(self):
        """初始化同僚代理人註冊表"""
        try:
            agents_ref = self.db.collection("agents")
            agents = agents_ref.where("status", "==", "DEPLOYED").stream()
            
            for agent in agents:
                agent_data = agent.to_dict()
                agent_id = agent_data.get("agent_id")
                if agent_id and agent_id != self.agent_name:
                    self.peer_agents[agent_id] = {
                        "agent_type": agent_data.get("agent_type"),
                        "role": agent_data.get("role"),
                        "capabilities": agent_data.get("capabilities", []),
                        "status": agent_data.get("status")
                    }
            
            logger.info(f"{self.agent_name} 載入了 {len(self.peer_agents)} 個同僚代理人")
            
        except Exception as e:
            logger.error(f"初始化同僚註冊表失敗: {e}")
    
    def handle_registry_update(self, message_data: Dict[str, Any]):
        """處理代理人註冊表更新"""
        try:
            event_type = message_data.get("event_type")
            data = message_data.get("data", {})
            
            if event_type == "PEER_AGENT_ADDED":
                agent_id = data.get("agent_id")
                if agent_id and agent_id != self.agent_name:
                    self.peer_agents[agent_id] = {
                        "agent_type": data.get("agent_type"),
                        "role": data.get("role"),
                        "capabilities": data.get("capabilities", []),
                        "status": data.get("status")
                    }
                    logger.info(f"{self.agent_name} 發現新的同僚代理人: {agent_id}")
            
            elif event_type == "PEER_AGENT_REMOVED":
                agent_id = data.get("agent_id")
                if agent_id in self.peer_agents:
                    del self.peer_agents[agent_id]
                    logger.info(f"{self.agent_name} 移除同僚代理人: {agent_id}")
            
            elif event_type == "PEER_AGENT_UPDATED":
                agent_id = data.get("agent_id")
                if agent_id and agent_id != self.agent_name:
                    self.peer_agents[agent_id] = {
                        "agent_type": data.get("agent_type"),
                        "role": data.get("role"),
                        "capabilities": data.get("capabilities", []),
                        "status": data.get("status")
                    }
                    logger.info(f"{self.agent_name} 更新同僚代理人: {agent_id}")
            
        except Exception as e:
            logger.error(f"處理註冊表更新失敗: {e}")
    
    def find_capable_peer(self, required_capabilities: List[str]) -> str:
        """根據所需能力找到合適的同僚代理人"""
        for agent_id, agent_info in self.peer_agents.items():
            agent_capabilities = agent_info.get("capabilities", [])
            if any(cap in agent_capabilities for cap in required_capabilities):
                return agent_id
        return None
    
    def get_peer_agents_summary(self) -> str:
        """獲取同僚代理人摘要"""
        if not self.peer_agents:
            return "目前沒有其他可用的代理人。"
        
        summary_parts = ["可用的同僚代理人："]
        for agent_id, agent_info in self.peer_agents.items():
            role = agent_info.get("role", "未知角色")
            capabilities = ", ".join(agent_info.get("capabilities", []))
            summary_parts.append(f"- {agent_id}: {role} (能力: {capabilities})")
        
        return "\n".join(summary_parts)
    
    async def forward_to_peer(self, peer_agent_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """將任務轉發給同僚代理人"""
        try:
            from app.shared_crew_lib.services.agent_communication_service import AgentCommunicationService
            
            comm_service = AgentCommunicationService()
            result = await comm_service.forward_task_to_agent(
                peer_agent_id, task_data, self.agent_name
            )
            
            return result
            
        except Exception as e:
            logger.error(f"轉發任務給同僚代理人失敗: {e}")
            return {"status": "ERROR", "error": str(e)}

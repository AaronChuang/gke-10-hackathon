from typing import Dict, Any, List, Optional
import logging
from google.cloud import firestore
from ..schemas.firestore_task import FirestoreTask, AgentHistoryEntry, TaskLogEntry, TokenUsage
from datetime import datetime

logger = logging.getLogger(__name__)

class TaskGuardrailService:
    """任務執行護欄服務 - 實現兩次重試終止邏輯和成本監控"""
    
    def __init__(self, db: firestore.Client):
        self.db = db
        self.max_retry_limit = 2  # 最多允許兩次重試
        self.max_token_limit = 10000  # 單個任務最大 Token 限制
    
    async def check_retry_limit(self, task_id: str, current_agent_id: str) -> bool:
        """
        檢查是否超過兩次重試限制
        返回 True 表示應該終止任務
        """
        try:
            task_doc = self.db.collection('tasks').document(task_id).get()
            if not task_doc.exists:
                logger.warning(f"任務 {task_id} 不存在")
                return False
            
            task_data = task_doc.to_dict()
            agent_history = task_data.get('agent_history', [])
            
            if len(agent_history) < self.max_retry_limit:
                return False
            
            # 檢查最後兩次執行是否為相同的代理人
            recent_history = agent_history[-self.max_retry_limit:]
            recent_agent_ids = [entry.get('agent_id') for entry in recent_history]
            
            # 如果當前代理人與最近兩次執行的代理人相同，則觸發終止
            if all(agent_id == current_agent_id for agent_id in recent_agent_ids):
                logger.warning(f"任務 {task_id} 觸發重試限制：代理人 {current_agent_id} 連續執行 {self.max_retry_limit} 次")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"檢查重試限制失敗: {e}")
            return False
    
    async def check_token_limit(self, task_id: str) -> bool:
        """
        檢查是否超過 Token 使用限制
        返回 True 表示應該終止任務
        """
        try:
            task_doc = self.db.collection('tasks').document(task_id).get()
            if not task_doc.exists:
                return False
            
            task_data = task_doc.to_dict()
            total_tokens = task_data.get('total_tokens', {'input_tokens': 0, 'output_tokens': 0})
            
            total_usage = total_tokens.get('input_tokens', 0) + total_tokens.get('output_tokens', 0)
            
            if total_usage > self.max_token_limit:
                logger.warning(f"任務 {task_id} 觸發 Token 限制：總使用量 {total_usage} 超過限制 {self.max_token_limit}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"檢查 Token 限制失敗: {e}")
            return False
    
    async def add_agent_history(self, task_id: str, agent_id: str, action: str, metadata: Dict[str, Any] = None):
        """添加代理人執行歷史記錄"""
        try:
            history_entry = AgentHistoryEntry(
                agent_id=agent_id,
                action=action,
                metadata=metadata or {}
            )
            
            self.db.collection('tasks').document(task_id).update({
                'agent_history': firestore.ArrayUnion([history_entry.model_dump()]),
                'updated_at': datetime.now().timestamp()
            })
            
            logger.info(f"添加代理人歷史：任務 {task_id}, 代理人 {agent_id}, 動作 {action}")
            
        except Exception as e:
            logger.error(f"添加代理人歷史失敗: {e}")
    
    async def log_task_event(self, task_id: str, event: str, agent_id: Optional[str] = None, 
                           token_usage: Optional[TokenUsage] = None, details: Dict[str, Any] = None):
        """記錄任務執行日誌"""
        try:
            log_entry = TaskLogEntry(
                event=event,
                agent_id=agent_id,
                token_usage=token_usage,
                details=details or {}
            )
            
            self.db.collection('tasks').document(task_id).update({
                'log': firestore.ArrayUnion([log_entry.model_dump()]),
                'updated_at': datetime.now().timestamp()
            })
            
            logger.info(f"記錄任務事件：任務 {task_id}, 事件 {event}")
            
        except Exception as e:
            logger.error(f"記錄任務事件失敗: {e}")
    
    async def update_total_tokens(self, task_id: str, token_usage: TokenUsage):
        """更新總 Token 消耗統計"""
        try:
            task_ref = self.db.collection('tasks').document(task_id)
            task_doc = task_ref.get()
            
            if task_doc.exists:
                current_tokens = task_doc.to_dict().get('total_tokens', {'input_tokens': 0, 'output_tokens': 0})
                new_total = TokenUsage(
                    input_tokens=current_tokens.get('input_tokens', 0) + token_usage.input_tokens,
                    output_tokens=current_tokens.get('output_tokens', 0) + token_usage.output_tokens
                )
                
                task_ref.update({
                    'total_tokens': new_total.model_dump(),
                    'updated_at': datetime.now().timestamp()
                })
                
                logger.info(f"更新 Token 統計：任務 {task_id}, 新增 {token_usage.input_tokens}/{token_usage.output_tokens}")
            
        except Exception as e:
            logger.error(f"更新 Token 統計失敗: {e}")
    
    async def terminate_task(self, task_id: str, reason: str, details: Dict[str, Any] = None):
        """終止任務執行"""
        try:
            termination_reasons = {
                "RETRY_LIMIT_EXCEEDED": "任務因超過兩次重試限制而終止",
                "TOKEN_LIMIT_EXCEEDED": "任務因超過 Token 使用限制而終止",
                "MANUAL_TERMINATION": "任務被手動終止",
                "ERROR": "任務因錯誤而終止"
            }
            
            error_message = termination_reasons.get(reason, f"任務因未知原因終止: {reason}")
            
            # 記錄終止事件
            await self.log_task_event(
                task_id, 
                f"任務終止: {reason}", 
                details=details or {}
            )
            
            # 更新任務狀態
            self.db.collection('tasks').document(task_id).update({
                'status': f"TERMINATED_BY_{reason}",
                'error': error_message,
                'updated_at': datetime.now().timestamp()
            })
            
            logger.warning(f"任務 {task_id} 已終止: {error_message}")
            
        except Exception as e:
            logger.error(f"終止任務失敗: {e}")
    
    async def should_terminate_task(self, task_id: str, current_agent_id: str) -> tuple[bool, Optional[str]]:
        """
        綜合檢查是否應該終止任務
        返回 (是否終止, 終止原因)
        """
        try:
            # 檢查重試限制
            if await self.check_retry_limit(task_id, current_agent_id):
                return True, "RETRY_LIMIT_EXCEEDED"
            
            # 檢查 Token 限制
            if await self.check_token_limit(task_id):
                return True, "TOKEN_LIMIT_EXCEEDED"
            
            return False, None
            
        except Exception as e:
            logger.error(f"檢查任務終止條件失敗: {e}")
            return False, None
    
    def get_task_statistics(self, task_id: str) -> Dict[str, Any]:
        """獲取任務統計資訊"""
        try:
            task_doc = self.db.collection('tasks').document(task_id).get()
            if not task_doc.exists:
                return {}
            
            task_data = task_doc.to_dict()
            
            # 統計代理人執行次數
            agent_history = task_data.get('agent_history', [])
            agent_counts = {}
            for entry in agent_history:
                agent_id = entry.get('agent_id')
                agent_counts[agent_id] = agent_counts.get(agent_id, 0) + 1
            
            # Token 使用統計
            total_tokens = task_data.get('total_tokens', {'input_tokens': 0, 'output_tokens': 0})
            
            # 執行時長
            created_at = task_data.get('created_at', 0)
            updated_at = task_data.get('updated_at', 0)
            duration_seconds = updated_at - created_at if updated_at > created_at else 0
            
            return {
                'task_id': task_id,
                'status': task_data.get('status', 'UNKNOWN'),
                'agent_execution_counts': agent_counts,
                'total_tokens': total_tokens,
                'total_token_usage': total_tokens.get('input_tokens', 0) + total_tokens.get('output_tokens', 0),
                'duration_seconds': duration_seconds,
                'log_entries_count': len(task_data.get('log', [])),
                'agent_history_count': len(agent_history)
            }
            
        except Exception as e:
            logger.error(f"獲取任務統計失敗: {e}")
            return {}

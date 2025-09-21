from typing import Dict, Any, List, Optional
import logging
from google.cloud import firestore
from ..schemas.firestore_task import FirestoreTask, AgentHistoryEntry, TaskLogEntry, TokenUsage
from datetime import datetime

logger = logging.getLogger(__name__)

class TaskGuardrailService:
    """Task execution guardrail service - Implements two-retry termination logic and cost monitoring"""
    
    def __init__(self, db: firestore.Client):
        self.db = db
        self.max_retry_limit = 2  # Maximum allowed retries
        self.max_token_limit = 10000  # Maximum token limit per task
    
    async def check_retry_limit(self, task_id: str, current_agent_id: str) -> bool:
        """
        Check if the two-retry limit has been exceeded
        Returns True if the task should be terminated
        """
        try:
            task_doc = self.db.collection('tasks').document(task_id).get()
            if not task_doc.exists:
                logger.warning(f"Task {task_id} does not exist")
                return False
            
            task_data = task_doc.to_dict()
            agent_history = task_data.get('agent_history', [])
            
            if len(agent_history) < self.max_retry_limit:
                return False
            
            # Check if the last two executions were by the same agent
            recent_history = agent_history[-self.max_retry_limit:]
            recent_agent_ids = [entry.get('agent_id') for entry in recent_history]
            
            # If current agent is the same as the last two executions, trigger termination
            if all(agent_id == current_agent_id for agent_id in recent_agent_ids):
                logger.warning(f"Task {task_id} triggered retry limit: agent {current_agent_id} executed {self.max_retry_limit} times consecutively")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check retry limit: {e}")
            return False
    
    async def check_token_limit(self, task_id: str) -> bool:
        """
        Check if token usage limit has been exceeded
        Returns True if the task should be terminated
        """
        try:
            task_doc = self.db.collection('tasks').document(task_id).get()
            if not task_doc.exists:
                return False
            
            task_data = task_doc.to_dict()
            total_tokens = task_data.get('total_tokens', {'input_tokens': 0, 'output_tokens': 0})
            
            total_usage = total_tokens.get('input_tokens', 0) + total_tokens.get('output_tokens', 0)
            
            if total_usage > self.max_token_limit:
                logger.warning(f"Task {task_id} triggered token limit: total usage {total_usage} exceeds limit {self.max_token_limit}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check token limit: {e}")
            return False
    
    async def add_agent_history(self, task_id: str, agent_id: str, action: str, metadata: Dict[str, Any] = None):
        """Add agent execution history record"""
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
            
            logger.info(f"Added agent history: task {task_id}, agent {agent_id}, action {action}")
            
        except Exception as e:
            logger.error(f"Failed to add agent history: {e}")
    
    async def log_task_event(self, task_id: str, event: str, agent_id: Optional[str] = None, 
                           token_usage: Optional[TokenUsage] = None, details: Dict[str, Any] = None):
        """Log task execution events"""
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
            
            logger.info(f"Logged task event: task {task_id}, event {event}")
            
        except Exception as e:
            logger.error(f"Failed to log task event: {e}")
    
    async def update_total_tokens(self, task_id: str, token_usage: TokenUsage):
        """Update total token consumption statistics"""
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
                
                logger.info(f"Updated token statistics: task {task_id}, added {token_usage.input_tokens}/{token_usage.output_tokens}")
            
        except Exception as e:
            logger.error(f"Failed to update token statistics: {e}")
    
    async def terminate_task(self, task_id: str, reason: str, details: Dict[str, Any] = None):
        """Terminate task execution"""
        try:
            termination_reasons = {
                "RETRY_LIMIT_EXCEEDED": "Task terminated due to exceeding two-retry limit",
                "TOKEN_LIMIT_EXCEEDED": "Task terminated due to exceeding token usage limit",
                "MANUAL_TERMINATION": "Task manually terminated",
                "ERROR": "Task terminated due to error"
            }
            
            error_message = termination_reasons.get(reason, f"Task terminated for unknown reason: {reason}")
            
            # Log termination event
            await self.log_task_event(
                task_id, 
                f"Task terminated: {reason}", 
                details=details or {}
            )
            
            # Update task status
            self.db.collection('tasks').document(task_id).update({
                'status': f"TERMINATED_BY_{reason}",
                'error': error_message,
                'updated_at': datetime.now().timestamp()
            })
            
            logger.warning(f"Task {task_id} terminated: {error_message}")
            
        except Exception as e:
            logger.error(f"Failed to terminate task: {e}")
    
    async def should_terminate_task(self, task_id: str, current_agent_id: str) -> tuple[bool, Optional[str]]:
        """
        Comprehensive check if task should be terminated
        Returns (should_terminate, termination_reason)
        """
        try:
            # Check retry limit
            if await self.check_retry_limit(task_id, current_agent_id):
                return True, "RETRY_LIMIT_EXCEEDED"
            
            # Check token limit
            if await self.check_token_limit(task_id):
                return True, "TOKEN_LIMIT_EXCEEDED"
            
            return False, None
            
        except Exception as e:
            logger.error(f"Failed to check task termination conditions: {e}")
            return False, None
    
    def get_task_statistics(self, task_id: str) -> Dict[str, Any]:
        """Get task statistics information"""
        try:
            task_doc = self.db.collection('tasks').document(task_id).get()
            if not task_doc.exists:
                return {}
            
            task_data = task_doc.to_dict()
            
            # Count agent execution times
            agent_history = task_data.get('agent_history', [])
            agent_counts = {}
            for entry in agent_history:
                agent_id = entry.get('agent_id')
                agent_counts[agent_id] = agent_counts.get(agent_id, 0) + 1
            
            # Token usage statistics
            total_tokens = task_data.get('total_tokens', {'input_tokens': 0, 'output_tokens': 0})
            
            # Execution duration
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
            logger.error(f"Failed to get task statistics: {e}")
            return {}

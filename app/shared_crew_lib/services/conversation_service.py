import uuid
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from google.cloud import firestore

from app.shared_crew_lib.clients import gcp_clients
from app.shared_crew_lib.schemas.conversation import (
    ConversationSession, 
    ConversationMessage, 
    MessageSender,
    ConversationStatus,
    ConversationContext
)

logger = logging.getLogger(__name__)

class ConversationService:
    
    def __init__(self):
        self.db = gcp_clients.get_firestore_client()
        self.collection_name = "conversations"
    
    async def create_session(
        self, 
        user_id: Optional[str] = None,
        context: Optional[ConversationContext] = None,
        session_id: Optional[str] = None
    ) -> ConversationSession:
        try:
            if not session_id:
                session_id = str(uuid.uuid4())
            
            if not context:
                context = ConversationContext(user_id=user_id)
            elif user_id and not context.user_id:
                context.user_id = user_id
            
            session = ConversationSession(
                session_id=session_id,
                context=context
            )

            doc_ref = self.db.collection(self.collection_name).document(session_id)
            doc_ref.set(session.model_dump())
            
            logger.info(f"Created conversation session: {session_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to create conversation session: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        try:
            doc_ref = self.db.collection(self.collection_name).document(session_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                return ConversationSession(**data)
            else:
                logger.warning(f"Conversation session not found: {session_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get conversation session {session_id}: {e}")
            return None
    
    async def add_message(
        self, 
        session_id: str, 
        sender: MessageSender, 
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[ConversationMessage]:
        try:
            session = await self.get_session(session_id)
            if not session:
                logger.error(f"Session not found: {session_id}")
                return None

            message = session.add_message(sender, content, metadata=metadata)
            
            doc_ref = self.db.collection(self.collection_name).document(session_id)
            doc_ref.update({
                'messages': firestore.ArrayUnion([message.model_dump()]),
                'updated_at': session.updated_at,
                'last_activity_at': session.last_activity_at,
                'summary': session.summary.model_dump()
            })
            
            logger.info(f"Added message to session {session_id}: {message.message_id}")
            return message
            
        except Exception as e:
            logger.error(f"Failed to add message to session {session_id}: {e}")
            return None
    
    async def get_conversation_history(
        self, 
        session_id: str, 
        limit: int = 10,
        format_for_ai: bool = False
    ) -> List[Dict[str, Any]]:
        try:
            session = await self.get_session(session_id)
            if not session:
                return []
            
            if format_for_ai:
                return session.get_conversation_history_for_ai(limit)
            else:
                recent_messages = session.get_recent_messages(limit)
                return [msg.model_dump() for msg in recent_messages]
                
        except Exception as e:
            logger.error(f"Failed to get conversation history for {session_id}: {e}")
            return []
    
    async def update_session_status(
        self, 
        session_id: str, 
        status: ConversationStatus
    ) -> bool:
        try:
            doc_ref = self.db.collection(self.collection_name).document(session_id)
            doc_ref.update({
                'status': status.value,
                'updated_at': datetime.now().timestamp()
            })
            
            logger.info(f"Updated session {session_id} status to {status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session status {session_id}: {e}")
            return False
    
    async def add_related_task(self, session_id: str, task_id: str) -> bool:
        try:
            doc_ref = self.db.collection(self.collection_name).document(session_id)
            doc_ref.update({
                'related_tasks': firestore.ArrayUnion([task_id]),
                'updated_at': datetime.now().timestamp()
            })
            
            logger.info(f"Added task {task_id} to session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add task to session {session_id}: {e}")
            return False
    
    async def get_active_sessions(self, user_id: Optional[str] = None) -> List[ConversationSession]:
        try:
            query = self.db.collection(self.collection_name).where('status', '==', ConversationStatus.ACTIVE.value)
            
            if user_id:
                query = query.where('context.user_id', '==', user_id)

            yesterday = datetime.now() - timedelta(days=1)
            query = query.where('last_activity_at', '>=', yesterday.timestamp())
            
            docs = query.stream()
            sessions = []
            
            for doc in docs:
                try:
                    session_data = doc.to_dict()
                    session = ConversationSession(**session_data)
                    sessions.append(session)
                except Exception as e:
                    logger.warning(f"Failed to parse session {doc.id}: {e}")
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get active sessions: {e}")
            return []
    
    async def cleanup_old_sessions(self, days_old: int = 30) -> int:
        try:
            cutoff_time = datetime.now() - timedelta(days=days_old)
            
            query = self.db.collection(self.collection_name).where(
                'last_activity_at', '<', cutoff_time.timestamp()
            ).where(
                'status', 'in', [ConversationStatus.COMPLETED.value, ConversationStatus.ARCHIVED.value]
            )
            
            docs = query.stream()
            deleted_count = 0
            
            for doc in docs:
                doc.reference.delete()
                deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old conversation sessions")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")
            return 0

import os
import uuid
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.shared_crew_lib.clients import gcp_clients
from app.shared_crew_lib.agents.proxy_agent import ProxyAgent
from app.shared_crew_lib.schemas.conversation_request import ConversationRequest, ConversationResponse
from app.shared_crew_lib.schemas.conversation import MessageSender
from app.shared_crew_lib.services.conversation_service import ConversationService
from app.shared_crew_lib.services.agent_communication_service import AgentCommunicationService
import logging

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")

if not PROJECT_ID:
    raise RuntimeError("Required environment variable not set: GCP_PROJECT_ID")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ProxyAgent - Intelligent Conversation Agent",
    description="Intelligent agent focused on customer conversations with task routing capabilities"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://35.236.185.81"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


db = gcp_clients.get_firestore_client()
publisher = gcp_clients.get_publisher_client()

proxy_agent = ProxyAgent()
communication_service = AgentCommunicationService()
conversation_service = ConversationService()

@app.get("/healthz", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}

@app.post("/conversation", status_code=status.HTTP_200_OK)
async def conversation(request: ConversationRequest) -> ConversationResponse:
    if not db or not publisher:
        raise HTTPException(status_code=500, detail="GCP clients not initialized, please check credentials.")

    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        session = await conversation_service.get_session(session_id)
        if not session:
            session = await conversation_service.create_session(
                session_id=session_id,
                user_id=request.user_id
            )
        
        user_message = await conversation_service.add_message(
            session_id=session_id,
            sender=MessageSender.USER,
            content=request.user_prompt
        )
        
        logger.info(f"Processing conversation in session: {session_id}")
        
        conversation_history = await conversation_service.get_conversation_history(
            session_id=session_id,
            limit=5,
            format_for_ai=True
        )
        
        product_context = request.product_context.model_dump() if request.product_context else None
        
        input_data = {
            "user_prompt": request.user_prompt,
            "conversation_history": conversation_history,
            "product_context": product_context
        }

        result = await proxy_agent.run(session_id, input_data)
        
        logger.info(f"ProxyAgent result: {result}")
        
        if result.get("status") == "COMPLETED":
            ai_response = result.get("output", "Sorry, I cannot process your request.")
            
            await conversation_service.add_message(
                session_id=session_id,
                sender=MessageSender.AI,
                content=ai_response
            )
            
            logger.info(f"AI response added to session: {session_id}")
            
            return ConversationResponse(
                task_id=session_id,
                agent_response=ai_response,
                action="DIRECT_REPLY",
                delegated_to=None,
                session_id=session_id
            )
            
        elif result.get("status") == "TASK_CREATED":
            task_id = result.get("task_id")
            
            if task_id:
                await conversation_service.add_related_task(session_id, task_id)
            
            return ConversationResponse(
                task_id=task_id or session_id,
                agent_response="Your request is being processed. You will be notified when it's complete.",
                action="TASK_DELEGATED",
                delegated_to=result.get("delegated_to"),
                session_id=session_id
            )
        
        else:
            error_msg = result.get("error", "Unknown error occurred while processing request")
            logger.error(f"ProxyAgent processing failed: {error_msg}")
            
            await conversation_service.add_message(
                session_id=session_id,
                sender=MessageSender.SYSTEM,
                content=f"Error: {error_msg}"
            )
            
            raise HTTPException(status_code=500, detail=error_msg)
            
    except Exception as e:
        error_msg = f"Conversation processing failed: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/conversation/{session_id}")
async def get_conversation(session_id: str, limit: int = 20):
    try:
        session = await conversation_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Conversation session not found")
        
        history = await conversation_service.get_conversation_history(
            session_id=session_id,
            limit=limit
        )
        
        return {
            "session_id": session_id,
            "status": session.status.value,
            "messages": history,
            "summary": session.summary.model_dump(),
            "related_tasks": session.related_tasks
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to get conversation: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

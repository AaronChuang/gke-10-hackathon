import os
import uuid
import logging
from contextlib import asynccontextmanager

from datetime import datetime
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from app.shared_crew_lib.clients import gcp_clients
from app.shared_crew_lib.agents.orchestrator_agent import OrchestratorAgent
from app.shared_crew_lib.schemas.agent_registry import CreateAgentRequest, AgentRegistryEntry
from app.shared_crew_lib.schemas.firestore_task import TaskType, TaskPriority, FirestoreTask
from app.shared_crew_lib.schemas.knowledge_base import IndexWebsiteRequest
from app.shared_crew_lib.services.agent_registry_service import AgentRegistryService
from typing import List, Dict, Any, Optional
from app.shared_crew_lib.services.conversation_service import ConversationService


load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
CRAWLER_TOPIC_ID = os.getenv("CRAWLER_TOPIC_ID")

if not all([PROJECT_ID, CRAWLER_TOPIC_ID]):
    raise RuntimeError("Required environment variables not set: GCP_PROJECT_ID, CRAWLER_TOPIC_ID")


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Agent Orchestrator",
    description="Intelligent conversation coordinator - understands user intent and intelligently routes tasks"
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

# 延遲初始化 agents，避免在模組載入時就失敗
orchestrator_agent = None
agent_registry_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator_agent, agent_registry_service

    try:
        logger.info("Initializing agents...")
        orchestrator_agent = OrchestratorAgent()
        agent_registry_service = AgentRegistryService()
        logger.info("Agents initialized successfully")

        await initialize_system()
    except Exception as e:
        logger.error(f"Failed to initialize agents during startup: {e}")
    yield


async def initialize_system():
    """Initialize system agents on startup"""
    try:

        # Then initialize the agent registry with default agents
        from app.shared_crew_lib.services.agent_initialization_service import AgentInitializationService
        init_service = AgentInitializationService()
        await init_service.initialize_default_agents()
        logger.info("System initialization completed successfully")
    except Exception as e:
        logger.error(f"System initialization failed: {e}")
        logger.warning("Service will continue running with limited functionality")


class TaskRequest(BaseModel):
    product_description: str

@app.get("/healthz", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}

@app.post("/api/start-task", status_code=status.HTTP_202_ACCEPTED)
async def start_task(request: TaskRequest):
    if not publisher or not db:
        raise HTTPException(status_code=500, detail="GCP clients not initialized")    
    try:
        # Create task in Firestore
        task_id = str(uuid.uuid4())
        task_data = {
            "task_id": task_id,
            "product_description": request.product_description,
            "status": "PENDING",
            "created_at": datetime.now().timestamp(),
            "updated_at": datetime.now().timestamp()
        }
        
        db.collection('tasks').document(task_id).set(task_data)
            
        result = await orchestrator_agent.run(task_id, {"product_description": request.product_description})
        
        return {"task_id": task_id, "message": "Task started successfully", "result": result}
        
    except Exception as e:
        logger.error(f"Failed to start task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start task: {str(e)}")


@app.get("/api/agents", response_model=List[AgentRegistryEntry])
async def get_agents():
    """Get all agents list"""
    try:
        agents = await agent_registry_service.get_all_agents()
        return agents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agents list: {str(e)}")

@app.post("/api/agents", status_code=status.HTTP_201_CREATED)
async def create_agent(request: CreateAgentRequest):
    """Create new agent"""
    try:
        # Ensure system is initialized before creating agents
        agent_id = await agent_registry_service.create_agent(request)
        return {"agent_id": agent_id, "message": "Agent created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")

@app.patch("/api/agents/{agent_id}")
async def update_agent(agent_id: str, updates: dict):
    """Update agent information"""
    try:
        success = await agent_registry_service.update_agent(agent_id, updates)
        if not success:
            raise HTTPException(status_code=404, detail="Agent does not exist")
        return {"message": "Agent updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update agent: {str(e)}")

@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete agent"""
    check_services_initialized()
    try:
        success = await agent_registry_service.delete_agent(agent_id)
        if not success:
            raise HTTPException(status_code=404, detail="Agent does not exist or cannot be deleted")
        return {"message": "Agent deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete agent: {str(e)}")


@app.post("/api/knowledge-base/index", status_code=status.HTTP_202_ACCEPTED)
async def index_website(request: IndexWebsiteRequest):
    """Publish a request to the crawler service to index a new website."""
    try:
        topic_path = publisher.topic_path(PROJECT_ID, CRAWLER_TOPIC_ID)
        message_data = request.model_dump_json().encode("utf-8")
        future = publisher.publish(topic_path, message_data)
        future.result()  # Wait for the publish to complete
        return {"message": "Website indexing request has been published."}
    except Exception as e:
        logger.error(f"Failed to publish indexing request: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to publish indexing request: {str(e)}")

@app.delete("/api/knowledge-base/{kb_id}", status_code=status.HTTP_200_OK)
async def delete_knowledge_entry(kb_id: str):
    """Deletes a knowledge base entry and all its associated data from Firestore."""
    try:
        # Reference to the main knowledge base document
        kb_doc_ref = db.collection('knowledge_base').document(kb_id)

        # Check if the document exists before proceeding
        if not (await kb_doc_ref.get()).exists:
            raise HTTPException(status_code=404, detail="Knowledge base entry not found.")

        # Delete all documents in the 'chunks' subcollection first
        chunks_ref = kb_doc_ref.collection('chunks')
        chunks_stream = chunks_ref.stream()
        async for chunk in chunks_stream:
            await chunk.reference.delete()
        
        # Finally, delete the main knowledge base document
        await kb_doc_ref.delete()

        logger.info(f"Successfully deleted knowledge base entry: {kb_id}")
        return {"message": "Knowledge base entry deleted successfully."}

    except HTTPException:
        raise # Re-raise HTTPException to preserve status code and detail
    except Exception as e:
        logger.error(f"Failed to delete knowledge base entry {kb_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete knowledge base entry: {str(e)}")


@app.post("/api/task", status_code=status.HTTP_201_CREATED)
async def create_task(
    task_type: TaskType,
    title: str,
    input_data: Dict[str, Any],
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    priority: TaskPriority = TaskPriority.MEDIUM,
    description: Optional[str] = None
):
    try:
        task_id = str(uuid.uuid4())
        
        task = FirestoreTask(
            task_id=task_id,
            task_type=task_type,
            title=title,
            description=description,
            input_data=input_data,
            priority=priority,
            conversation_session_id=session_id,
            user_id=user_id
        )
        
        db.collection('tasks').document(task_id).set(task.model_dump())

        if session_id:
            conversation_service = ConversationService()
            await conversation_service.add_related_task(session_id, task_id)
        
        logger.info(f"Created task: {task_id}")
        
        return {
            "task_id": task_id,
            "status": task.status.value,
            "message": "Task created successfully"
        }
        
    except Exception as e:
        error_msg = f"Failed to create task: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/api/task/{task_id}")
async def get_task(task_id: str):
    try:
        doc_ref = db.collection('tasks').document(task_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task_data = doc.to_dict()
        return task_data
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to get task: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
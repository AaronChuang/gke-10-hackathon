import os
import uuid
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from dotenv import load_dotenv
from app.shared_crew_lib.clients import gcp_clients
from app.shared_crew_lib.schemas.agent_task_message import AgentTaskMessage
from app.shared_crew_lib.schemas.firestore_task import FirestoreTask
from app.shared_crew_lib.agents.orchestrator_agent import OrchestratorAgent
from app.shared_crew_lib.schemas.agent_registry import CreateAgentRequest, AgentRegistryEntry
from app.shared_crew_lib.schemas.knowledge_base import IndexWebsiteRequest, KnowledgeBaseEntry
from app.shared_crew_lib.services.agent_registry_service import AgentRegistryService
from app.services.crawler_service import CrawlerService
from typing import List

load_dotenv()

app = FastAPI(
    title="AI Agent Orchestrator",
    description="智能對話協調員 - 理解用戶意圖並智能路由任務"
)

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
TECH_ANALYST_TOPIC_ID = os.getenv("TECH_ANALYST_TOPIC_ID")
STYLIST_TOPIC_ID = os.getenv("STYLIST_TOPIC_ID")

if not all([PROJECT_ID, TECH_ANALYST_TOPIC_ID, STYLIST_TOPIC_ID]):
    raise RuntimeError("必要的環境變數未設定：GCP_PROJECT_ID, TECH_ANALYST_TOPIC_ID, STYLIST_TOPIC_ID")

publisher = gcp_clients.get_publisher_client()
db = gcp_clients.get_firestore_client()

# 初始化服務
orchestrator_agent = OrchestratorAgent()
agent_registry_service = AgentRegistryService()
crawler_service = CrawlerService()

# 保留舊的 API 以向後兼容
class TaskRequest(BaseModel):
    product_description: str

@app.get("/healthz", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}

@app.post("/api/start-task", status_code=status.HTTP_202_ACCEPTED)
async def start_task(request: TaskRequest):
    if not publisher or not db:
        raise HTTPException(status_code=500, detail="GCP 客戶端尚未初始化，請檢查憑證。")

    task_id = str(uuid.uuid4())

    try:
        task_data = FirestoreTask(
            task_id=task_id,
            status="PENDING",
            initial_request=request.model_dump(),
        )
        db.collection('tasks').document(task_id).set(task_data.model_dump())
        print(f"已為 task_id 創建 Firestore 記錄: {task_id}")

        message_to_publish = AgentTaskMessage(
            task_id=task_id,
            input_data={"product_description": request.product_description}
        )

        # 預設發送到 tech analyst topic (向後兼容)
        tech_topic_path = publisher.topic_path(PROJECT_ID, TECH_ANALYST_TOPIC_ID)
        future = publisher.publish(tech_topic_path, message_to_publish.model_dump_json().encode('utf-8'))
        message_id = future.result()
        print(f"已發布訊息 {message_id} 到 {tech_topic_path} (任務ID: {task_id})")

    except Exception as e:
        print(f"啟動任務 {task_id} 失敗: {e}")
        raise HTTPException(status_code=500, detail=f"觸發 AI 任務失敗: {str(e)}")

    return {"message": "任務已成功啟動", "task_id": task_id}


# ==================== 代理人管理 API ====================

@app.get("/api/agents", response_model=List[AgentRegistryEntry])
async def get_agents():
    """獲取所有代理人列表"""
    try:
        agents = await agent_registry_service.get_all_agents()
        return agents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取代理人列表失敗: {str(e)}")

@app.post("/api/agents", status_code=status.HTTP_201_CREATED)
async def create_agent(request: CreateAgentRequest):
    """創建新代理人"""
    try:
        agent_id = await agent_registry_service.create_agent(request)
        return {"message": "代理人創建成功", "agent_id": agent_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"創建代理人失敗: {str(e)}")

@app.patch("/api/agents/{agent_id}")
async def update_agent(agent_id: str, updates: dict):
    """更新代理人信息"""
    try:
        success = await agent_registry_service.update_agent(agent_id, updates)
        if not success:
            raise HTTPException(status_code=404, detail="代理人不存在")
        return {"message": "代理人更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新代理人失敗: {str(e)}")

@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """刪除代理人"""
    try:
        success = await agent_registry_service.delete_agent(agent_id)
        if not success:
            raise HTTPException(status_code=404, detail="代理人不存在或無法刪除")
        return {"message": "代理人刪除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刪除代理人失敗: {str(e)}")


# ==================== 知識庫管理 API ====================

@app.get("/api/knowledge-base", response_model=List[KnowledgeBaseEntry])
async def get_knowledge_base():
    """獲取知識庫列表"""
    try:
        entries = await crawler_service.get_all_knowledge_entries()
        return entries
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取知識庫列表失敗: {str(e)}")

@app.post("/api/knowledge-base/index", status_code=status.HTTP_202_ACCEPTED)
async def index_website(request: IndexWebsiteRequest):
    """索引新網站"""
    try:
        kb_id = await crawler_service.start_crawling(request.url)
        return {"message": "網站索引已開始", "kb_id": kb_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"開始索引失敗: {str(e)}")

@app.post("/api/knowledge-base/reindex/{kb_id}", status_code=status.HTTP_202_ACCEPTED)
async def reindex_website(kb_id: str):
    """重新索引網站"""
    try:
        success = await crawler_service.reindex_website(kb_id)
        if not success:
            raise HTTPException(status_code=404, detail="知識庫項目不存在")
        return {"message": "重新索引已開始"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新索引失敗: {str(e)}")

@app.delete("/api/knowledge-base/{kb_id}")
async def delete_knowledge_entry(kb_id: str):
    """刪除知識庫項目"""
    try:
        success = await crawler_service.delete_knowledge_entry(kb_id)
        if not success:
            raise HTTPException(status_code=404, detail="知識庫項目不存在")
        return {"message": "知識庫項目刪除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刪除知識庫項目失敗: {str(e)}")

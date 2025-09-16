import os
import uuid
from fastapi import FastAPI, HTTPException, status
from dotenv import load_dotenv
from datetime import datetime
from app.shared_crew_lib.clients import gcp_clients
from app.shared_crew_lib.agents.proxy_agent import ProxyAgent
from app.shared_crew_lib.schemas.conversation_request import ConversationRequest, ConversationResponse, \
    ConversationMessage
from app.shared_crew_lib.schemas.firestore_task import FirestoreTask
from app.shared_crew_lib.services.agent_communication_service import AgentCommunicationService
import logging

load_dotenv()

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ProxyAgent - 智能對話代理人",
    description="專注於客戶對話的智能代理人，具備任務路由能力"
)

PROJECT_ID = os.getenv("GCP_PROJECT_ID")

if not PROJECT_ID:
    raise RuntimeError("必要的環境變數未設定：GCP_PROJECT_ID")

# 初始化客戶端
db = gcp_clients.get_firestore_client()
publisher = gcp_clients.get_publisher_client()

# 初始化服務
proxy_agent = ProxyAgent()
communication_service = AgentCommunicationService()

@app.get("/healthz", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}

@app.post("/api/conversation", status_code=status.HTTP_200_OK)
async def conversation(request: ConversationRequest) -> ConversationResponse:
    """智能對話 API - 由 ProxyAgent 處理並判斷是否需要轉發"""
    if not db or not publisher:
        raise HTTPException(status_code=500, detail="GCP 客戶端尚未初始化，請檢查憑證。")

    try:
        # 生成任務 ID
        task_id = str(uuid.uuid4())
        
        # 創建對話訊息
        user_message = ConversationMessage(sender="user", text=request.user_prompt)
        
        logger.info(f"ProxyAgent 處理對話: {task_id}")
        
        # 使用 ProxyAgent 處理對話
        conversation_history = [msg.model_dump() for msg in request.conversation_history]
        product_context = request.product_context.model_dump() if request.product_context else None
        
        input_data = {
            "user_prompt": request.user_prompt,
            "conversation_history": conversation_history,
            "product_context": product_context
        }
        
        # 執行 ProxyAgent 任務
        result = await proxy_agent.run(task_id, input_data)
        
        if result.get("status") == "COMPLETED":
            ai_response = result.get("output", "抱歉，我無法處理您的請求。")
            
            # 檢查是否需要轉發給其他代理人
            should_forward, target_agent, required_capabilities = proxy_agent.should_forward_task(request.user_prompt)
            
            if should_forward:
                # 尋找合適的代理人
                if not target_agent:
                    suitable_agent = await communication_service.find_suitable_agent(
                        request.user_prompt, required_capabilities
                    )
                    if suitable_agent:
                        target_agent = suitable_agent["agent_id"]
                
                if target_agent:
                    # 轉發任務
                    forward_result = await communication_service.forward_task_to_agent(
                        target_agent, {
                            "task_id": task_id,
                            "input_data": input_data
                        }, "proxy-agent"
                    )
                    
                    if forward_result.get("status") == "SUCCESS":
                        ai_response = f"我已將您的請求轉發給專業的 {target_agent} 處理，請稍候片刻。"
                        action = "FORWARDED"
                        delegated_to = target_agent
                    else:
                        ai_response = f"轉發失敗，我將直接為您處理：{ai_response}"
                        action = "DIRECT_REPLY"
                        delegated_to = None
                else:
                    # 找不到合適的代理人，直接回覆
                    action = "DIRECT_REPLY"
                    delegated_to = None
            else:
                # 不需要轉發，直接回覆
                action = "DIRECT_REPLY"
                delegated_to = None
            
            # 創建 AI 回應訊息
            ai_message = ConversationMessage(sender="ai", text=ai_response)
            
            # 儲存對話記錄
            task_data = FirestoreTask(
                task_id=task_id,
                status="COMPLETED" if action == "DIRECT_REPLY" else "FORWARDED",
                user_id=request.user_id,
                initial_request={"user_prompt": request.user_prompt},
                conversation_history=[user_message, ai_message],
                product_context=product_context,
                completed_at=datetime.now().timestamp() if action == "DIRECT_REPLY" else None
            )
            
            db.collection('tasks').document(task_id).set(task_data.model_dump())
            
            return ConversationResponse(
                task_id=task_id,
                agent_response=ai_response,
                action=action,
                delegated_to=delegated_to
            )
        
        else:
            # 處理失敗
            error_msg = result.get("error", "處理請求時發生未知錯誤")
            logger.error(f"ProxyAgent 處理失敗: {error_msg}")
            
            return ConversationResponse(
                task_id=task_id,
                agent_response="抱歉，我現在無法處理您的請求，請稍後再試。",
                action="ERROR"
            )
            
    except Exception as e:
        logger.error(f"對話處理失敗: {e}")
        raise HTTPException(status_code=500, detail=f"對話處理失敗: {str(e)}")

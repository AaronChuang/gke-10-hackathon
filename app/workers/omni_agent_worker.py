import os
import json
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from google.cloud import pubsub_v1
from dotenv import load_dotenv

from app.shared_crew_lib.clients import gcp_clients
from app.shared_crew_lib.agents.omni_agent import OmniAgent
from app.shared_crew_lib.schemas.agent_task_message import AgentTaskMessage

# 載入環境變數
load_dotenv()

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 環境變數
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
AGENT_SUBSCRIPTION_ID = os.getenv("AGENT_SUBSCRIPTION_ID")

if not all([PROJECT_ID, AGENT_SUBSCRIPTION_ID]):
    raise RuntimeError("必要的環境變數未設定：GCP_PROJECT_ID, AGENT_SUBSCRIPTION_ID")

# 初始化客戶端
subscriber = gcp_clients.get_subscriber_client()
db = gcp_clients.get_firestore_client()

class OmniAgentWorker:
    """OmniAgent 工作者 - 處理可配置的通用任務"""
    
    def __init__(self):
        self.subscription_path = subscriber.subscription_path(PROJECT_ID, AGENT_SUBSCRIPTION_ID)
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    async def process_message(self, message):
        """處理單個消息"""
        try:
            # 解析消息
            message_data = json.loads(message.data.decode('utf-8'))
            
            # 檢查是否為註冊表更新消息
            if message.attributes.get('message_type') == 'registry_update':
                await self._handle_registry_update(message_data)
                message.ack()
                return
            
            task_message = AgentTaskMessage(**message_data)
            
            logger.info(f"處理 OmniAgent 任務: {task_message.task_id}")
            
            # 從任務數據中提取配置參數
            input_data = task_message.input_data
            custom_role = input_data.get('custom_role', '通用助手')
            custom_goal = input_data.get('custom_goal', '協助用戶完成各種任務')
            custom_backstory = input_data.get('custom_backstory', '你是一個靈活的AI助手，能夠適應各種不同的任務需求。')
            
            # 創建 OmniAgent 實例
            agent = OmniAgent(
                task_id=task_message.task_id,
                output_field="omni_agent_output",
                custom_role=custom_role,
                custom_goal=custom_goal,
                custom_backstory=custom_backstory
            )
            
            # 保存當前代理人實例以便處理註冊表更新
            self.current_agent = agent
            
            # 執行任務
            result = await agent.run(task_message.task_id, input_data)
            
            if result.get("status") == "COMPLETED":
                logger.info(f"OmniAgent 任務完成: {task_message.task_id}")
                message.ack()
            else:
                logger.error(f"OmniAgent 任務失敗: {task_message.task_id}, 錯誤: {result.get('error')}")
                message.nack()
                
        except Exception as e:
            logger.error(f"處理消息失敗: {e}")
            message.nack()
    
    async def _handle_registry_update(self, message_data):
        """處理代理人註冊表更新"""
        try:
            # 更新本地代理人註冊表
            if hasattr(self, 'current_agent') and self.current_agent:
                self.current_agent.handle_registry_update(message_data)
            
            logger.info(f"OmniAgent Worker 處理註冊表更新: {message_data.get('event_type')}")
            
        except Exception as e:
            logger.error(f"處理註冊表更新失敗: {e}")
    
    def message_callback(self, message):
        """Pub/Sub 消息回調"""
        # 使用 asyncio 運行異步處理函數
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.process_message(message))
        finally:
            loop.close()
    
    def start_listening(self):
        """開始監聽消息"""
        logger.info(f"OmniAgent Worker 開始監聽: {self.subscription_path}")
        
        # 配置流控制
        flow_control = pubsub_v1.types.FlowControl(max_messages=10)
        
        # 開始拉取消息
        streaming_pull_future = subscriber.subscribe(
            self.subscription_path,
            callback=self.message_callback,
            flow_control=flow_control
        )
        
        logger.info("OmniAgent Worker 正在運行...")
        
        try:
            streaming_pull_future.result()
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            logger.info("OmniAgent Worker 已停止")

def main():
    """主函數"""
    worker = OmniAgentWorker()
    worker.start_listening()

if __name__ == "__main__":
    main()

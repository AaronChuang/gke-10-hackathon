import os
import json
import asyncio
import logging
from typing import Dict, Any
from google.cloud import pubsub_v1
from dotenv import load_dotenv

from app.shared_crew_lib.clients import gcp_clients

# 載入環境變數
load_dotenv()

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 環境變數
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
REGISTRY_SUBSCRIPTION_ID = os.getenv("AGENT_REGISTRY_SUBSCRIPTION_ID", "agent-registry-updates-sub")

if not PROJECT_ID:
    raise RuntimeError("必要的環境變數未設定：GCP_PROJECT_ID")

# 初始化客戶端
subscriber = gcp_clients.get_subscriber_client()
db = gcp_clients.get_firestore_client()

class AgentRegistryListener:
    """代理人註冊表監聽器"""
    
    def __init__(self):
        self.subscription_path = subscriber.subscription_path(PROJECT_ID, REGISTRY_SUBSCRIPTION_ID)
        self.local_agent_registry = {}
        
    async def initialize_local_registry(self):
        """初始化本地代理人註冊表"""
        try:
            agents_ref = db.collection("agents")
            agents = agents_ref.where("status", "==", "DEPLOYED").stream()
            
            for agent in agents:
                agent_data = agent.to_dict()
                self.local_agent_registry[agent_data["agent_id"]] = agent_data
                
            logger.info(f"初始化本地註冊表，載入 {len(self.local_agent_registry)} 個代理人")
            
        except Exception as e:
            logger.error(f"初始化本地註冊表失敗: {e}")
    
    async def process_registry_update(self, message):
        """處理註冊表更新消息"""
        try:
            # 解析消息
            message_data = json.loads(message.data.decode('utf-8'))
            action = message_data.get("action")
            agent_data = message_data.get("agent_data", {})
            
            logger.info(f"處理註冊表更新: {action} - {agent_data.get('agent_id', 'unknown')}")
            
            if action == "AGENT_ADDED":
                await self._handle_agent_added(agent_data)
            elif action == "AGENT_REMOVED":
                await self._handle_agent_removed(agent_data)
            elif action == "AGENT_UPDATED":
                await self._handle_agent_updated(agent_data)
            else:
                logger.warning(f"未知的註冊表更新動作: {action}")
            
            message.ack()
            
        except Exception as e:
            logger.error(f"處理註冊表更新失敗: {e}")
            message.nack()
    
    async def _handle_agent_added(self, agent_data: Dict[str, Any]):
        """處理代理人新增"""
        agent_id = agent_data.get("agent_id")
        if agent_id:
            self.local_agent_registry[agent_id] = agent_data
            logger.info(f"新增代理人到本地註冊表: {agent_id}")
            
            # 通知所有代理人有新的代理人加入
            await self._broadcast_to_all_agents("PEER_AGENT_ADDED", agent_data)
    
    async def _handle_agent_removed(self, agent_data: Dict[str, Any]):
        """處理代理人移除"""
        agent_id = agent_data.get("agent_id")
        if agent_id and agent_id in self.local_agent_registry:
            del self.local_agent_registry[agent_id]
            logger.info(f"從本地註冊表移除代理人: {agent_id}")
            
            # 通知所有代理人有代理人被移除
            await self._broadcast_to_all_agents("PEER_AGENT_REMOVED", {"agent_id": agent_id})
    
    async def _handle_agent_updated(self, agent_data: Dict[str, Any]):
        """處理代理人更新"""
        agent_id = agent_data.get("agent_id")
        if agent_id:
            self.local_agent_registry[agent_id] = agent_data
            logger.info(f"更新本地註冊表中的代理人: {agent_id}")
            
            # 通知所有代理人有代理人被更新
            await self._broadcast_to_all_agents("PEER_AGENT_UPDATED", agent_data)
    
    async def _broadcast_to_all_agents(self, event_type: str, data: Dict[str, Any]):
        """向所有代理人廣播事件"""
        try:
            publisher = gcp_clients.get_publisher_client()
            
            broadcast_message = {
                "event_type": event_type,
                "data": data,
                "registry_snapshot": list(self.local_agent_registry.keys())
            }
            
            # 向每個代理人的主題發送消息
            for agent_id in self.local_agent_registry.keys():
                try:
                    topic_path = publisher.topic_path(PROJECT_ID, f"{agent_id}-topic")
                    
                    future = publisher.publish(
                        topic_path,
                        json.dumps(broadcast_message).encode('utf-8'),
                        message_type="registry_update"
                    )
                    
                    future.result()  # 等待發送完成
                    
                except Exception as e:
                    logger.warning(f"向代理人 {agent_id} 廣播失敗: {e}")
            
            logger.info(f"廣播事件完成: {event_type}")
            
        except Exception as e:
            logger.error(f"廣播事件失敗: {e}")
    
    def message_callback(self, message):
        """Pub/Sub 消息回調"""
        # 使用 asyncio 運行異步處理函數
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.process_registry_update(message))
        finally:
            loop.close()
    
    def start_listening(self):
        """開始監聽註冊表更新"""
        logger.info(f"代理人註冊表監聽器開始監聽: {self.subscription_path}")
        
        # 配置流控制
        flow_control = pubsub_v1.types.FlowControl(max_messages=10)
        
        # 開始拉取消息
        streaming_pull_future = subscriber.subscribe(
            self.subscription_path,
            callback=self.message_callback,
            flow_control=flow_control
        )
        
        logger.info("代理人註冊表監聽器正在運行...")
        
        try:
            streaming_pull_future.result()
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            logger.info("代理人註冊表監聽器已停止")

async def main():
    """主函數"""
    listener = AgentRegistryListener()
    
    # 初始化本地註冊表
    await listener.initialize_local_registry()
    
    # 開始監聽
    listener.start_listening()

if __name__ == "__main__":
    asyncio.run(main())

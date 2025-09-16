from typing import List, Optional
import logging
from google.cloud import firestore
from ..schemas.agent_registry import AgentRegistryEntry, AgentStatus
from datetime import datetime

logger = logging.getLogger(__name__)

class AgentRegistryService:
    """代理人註冊表服務 - 管理動態 Agent 創建和發現"""
    
    def __init__(self, db: firestore.Client):
        self.db = db
        self.collection_name = "agents"
    
    async def get_all_agents(self) -> List[AgentRegistryEntry]:
        """獲取所有註冊的代理人"""
        try:
            docs = self.db.collection(self.collection_name).stream()
            agents = []
            
            for doc in docs:
                agent_data = doc.to_dict()
                agents.append(AgentRegistryEntry(**agent_data))
            
            return agents
        except Exception as e:
            logger.error(f"獲取代理人列表失敗: {e}")
            return []
    
    async def get_active_agents(self) -> List[AgentRegistryEntry]:
        """獲取所有活躍的代理人"""
        try:
            docs = self.db.collection(self.collection_name).where(
                "status", "==", AgentStatus.ACTIVE.value
            ).stream()
            
            agents = []
            for doc in docs:
                agent_data = doc.to_dict()
                agents.append(AgentRegistryEntry(**agent_data))
            
            return agents
        except Exception as e:
            logger.error(f"獲取活躍代理人列表失敗: {e}")
            return []
    
    async def get_agent_by_id(self, agent_id: str) -> Optional[AgentRegistryEntry]:
        """根據 ID 獲取特定代理人"""
        try:
            doc = self.db.collection(self.collection_name).document(agent_id).get()
            
            if doc.exists:
                return AgentRegistryEntry(**doc.to_dict())
            return None
        except Exception as e:
            logger.error(f"獲取代理人 {agent_id} 失敗: {e}")
            return None
    
    async def create_agent_entry(self, agent: AgentRegistryEntry) -> bool:
        """創建新的代理人註冊項目"""
        try:
            agent_dict = agent.model_dump()
            agent_dict["updated_at"] = datetime.now().timestamp()
            
            self.db.collection(self.collection_name).document(agent.agent_id).set(agent_dict)
            logger.info(f"成功創建代理人: {agent.agent_id}")
            return True
        except Exception as e:
            logger.error(f"創建代理人失敗: {e}")
            return False
    
    async def update_agent_status(self, agent_id: str, status: AgentStatus, error_message: Optional[str] = None) -> bool:
        """更新代理人狀態"""
        try:
            update_data = {
                "status": status.value,
                "updated_at": datetime.now().timestamp()
            }
            
            if error_message:
                update_data["metadata.error_message"] = error_message
            
            self.db.collection(self.collection_name).document(agent_id).update(update_data)
            logger.info(f"更新代理人 {agent_id} 狀態為: {status.value}")
            return True
        except Exception as e:
            logger.error(f"更新代理人狀態失敗: {e}")
            return False
    
    async def delete_agent(self, agent_id: str) -> bool:
        """刪除代理人 (除了 OrchestratorAgent)"""
        if agent_id == "orchestrator-agent":
            logger.warning("不能刪除 OrchestratorAgent")
            return False
        
        try:
            self.db.collection(self.collection_name).document(agent_id).delete()
            logger.info(f"成功刪除代理人: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"刪除代理人失敗: {e}")
            return False
    
    async def find_agents_by_capability(self, capability: str) -> List[AgentRegistryEntry]:
        """根據能力標籤查找代理人"""
        try:
            docs = self.db.collection(self.collection_name).where(
                "capabilities", "array_contains", capability
            ).where("status", "==", AgentStatus.ACTIVE.value).stream()
            
            agents = []
            for doc in docs:
                agent_data = doc.to_dict()
                agents.append(AgentRegistryEntry(**agent_data))
            
            return agents
        except Exception as e:
            logger.error(f"根據能力查找代理人失敗: {e}")
            return []
    
    async def initialize_default_agents(self):
        """初始化預設的代理人 (OrchestratorAgent, StylistAgent, TechAnalystAgent)"""
        default_agents = [
            AgentRegistryEntry(
                agent_id="orchestrator-agent",
                name="智慧協調者",
                description="負責意圖識別、任務路由和代理人管理的核心智慧大腦",
                system_prompt="你是一個智慧的任務協調者，負責分析用戶意圖並將任務委派給最適合的專家代理人。你的所有回答都必須嚴格基於提供的上下文。",
                pubsub_topic="orchestrator-topic",
                capabilities=["intent_recognition", "task_routing", "agent_management"],
                metadata={"is_core_agent": True, "deletable": False}
            ),
            AgentRegistryEntry(
                agent_id="stylist-agent",
                name="AI 造型師",
                description="專門為服飾提供時尚搭配建議的專家",
                system_prompt="你是一位頂尖的時尚造型師，專門為客戶提供個性化的服飾搭配建議。你的所有回答都必須嚴格基於提供的上下文。如果上下文中沒有相關資訊，你必須明確告知使用者你不知道，嚴禁捏造任何資訊。",
                pubsub_topic="stylist-topic",
                capabilities=["fashion_advice", "style_consultation", "outfit_recommendation"]
            ),
            AgentRegistryEntry(
                agent_id="tech-analyst-agent",
                name="技術分析師",
                description="專門進行產品技術分析和規格評估的專家",
                system_prompt="你是一位專業的技術分析師，專門分析產品的技術規格、性能特點和市場定位。你的所有回答都必須嚴格基於提供的上下文。如果上下文中沒有相關資訊，你必須明確告知使用者你不知道，嚴禁捏造任何資訊。",
                pubsub_topic="tech-analyst-topic",
                capabilities=["technical_analysis", "product_evaluation", "specification_review"]
            )
        ]
        
        for agent in default_agents:
            existing_agent = await self.get_agent_by_id(agent.agent_id)
            if not existing_agent:
                await self.create_agent_entry(agent)
                logger.info(f"初始化預設代理人: {agent.name}")
            else:
                logger.info(f"預設代理人已存在: {agent.name}")
    
    def get_agents_summary_for_orchestrator(self) -> str:
        """為 OrchestratorAgent 提供代理人能力摘要"""
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            agents = loop.run_until_complete(self.get_active_agents())
            
            if not agents:
                return "目前沒有可用的專家代理人。"
            
            summary_parts = ["目前可用的專家代理人："]
            
            for agent in agents:
                if agent.agent_id != "orchestrator-agent":  # 排除自己
                    capabilities_str = ", ".join(agent.capabilities) if agent.capabilities else "通用"
                    summary_parts.append(
                        f"- {agent.name} ({agent.agent_id}): {agent.description}\n"
                        f"  能力: {capabilities_str}"
                    )
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"獲取代理人摘要失敗: {e}")
            return "無法獲取代理人資訊。"

from crewai import Agent, Task
from typing import Dict, Any, Optional
from enum import Enum
from .base import BaseAgentWrapper
from app.shared_crew_lib.services.agent_deployment_service import AgentDeploymentService, AgentInfo
from app.shared_crew_lib.services.agent_communication_service import AgentCommunicationService
import logging

logger = logging.getLogger(__name__)

class IntentType(Enum):
    """意圖類型枚舉"""
    SIMPLE_GREETING = "SIMPLE_GREETING"
    PRODUCT_INQUIRY = "PRODUCT_INQUIRY"
    STYLE_ADVICE = "STYLE_ADVICE"
    TECHNICAL_ANALYSIS = "TECHNICAL_ANALYSIS"
    AGENT_MANAGEMENT = "AGENT_MANAGEMENT"
    AGENT_CREATION = "AGENT_CREATION"
    AGENT_DELETION = "AGENT_DELETION"
    AGENT_QUERY = "AGENT_QUERY"
    TASK_FORWARDING = "TASK_FORWARDING"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class OrchestratorAgent(BaseAgentWrapper):
    """協調代理人 - 負責意圖識別和任務路由"""
    
    def __init__(self, task_id: str = None, output_field: str = None):
        super().__init__("orchestrator-agent", task_id, output_field)
        self.deployment_service = AgentDeploymentService()
        self.communication_service = AgentCommunicationService()
    
    def create_agent(self) -> Agent:
        """創建協調代理人實例"""
        return Agent(
            role="智慧任務協調者與代理人管理員",
            goal="準確識別用戶意圖，智慧路由任務，並管理代理人生命週期",
            backstory="""你是一個經驗豐富的任務協調專家和代理人管理員。
            你能夠識別各種用戶意圖，包括簡單問候、產品詢問、專業諮詢需求，以及代理人管理請求。
            你具備以下核心能力：
            1. 意圖識別和任務路由
            2. 代理人創建規劃（需用戶確認後執行）
            3. 代理人刪除和資源清理
            4. 代理人間通信協調
            5. 動態發現和管理代理人註冊表
            
            當用戶請求創建新代理人時，你會：
            - 分析需求並設計代理人規格
            - 提供詳細的創建計劃
            - 等待用戶確認後執行部署
            - 創建對應的 Pub/Sub 資源和 K8s 部署
            
            你的所有回答都基於可靠的知識庫，絕不捏造資訊。
            請保持回應簡潔明確，避免過度冗長。""",
            llm=self.llm,
            allow_delegation=False,
            verbose=True
        )
    
    def create_task(self, input_data: Dict[str, Any]) -> Task:
        """創建意圖分析任務"""
        user_prompt = input_data.get('user_prompt', '')
        conversation_history = input_data.get('conversation_history', [])
        product_context = input_data.get('product_context', {})
        
        # 構建上下文
        context_parts = [f"用戶輸入：{user_prompt}"]
        
        if conversation_history:
            context_parts.append("\n對話歷史：")
            for msg in conversation_history[-3:]:
                sender = "用戶" if msg.get("sender") == "user" else "AI"
                context_parts.append(f"{sender}: {msg.get('text', '')}")
        
        if product_context:
            context_parts.append(f"\n當前商品：{product_context.get('name', '')} - {product_context.get('description', '')}")
        
        context = "\n".join(context_parts)
        
        return Task(
            description=f"""
            分析以下用戶輸入的意圖，並提供適當的回應：

            {context}

            請根據以下分類判斷意圖：
            1. SIMPLE_GREETING - 簡單問候、感謝或閒聊
            2. PRODUCT_INQUIRY - 關於當前商品的基本資訊查詢
            3. STYLE_ADVICE - 尋求造型、搭配相關建議
            4. TECHNICAL_ANALYSIS - AI 技術、架構分析請求
            5. AGENT_CREATION - 請求創建新的代理人
            6. AGENT_DELETION - 請求刪除現有代理人
            7. AGENT_QUERY - 查詢現有代理人狀態或列表
            8. TASK_FORWARDING - 需要轉發給其他代理人的任務
            9. OUT_OF_SCOPE - 超出業務範圍的請求

            對於代理人管理請求，請提供詳細的執行計劃並等待用戶確認。
            對於需要專業建議的請求，請說明需要轉交給相關專家。
            """,
            expected_output="基於意圖分析的適當回應",
            agent=self.agent
        )
    
    async def handle_agent_management(self, intent: IntentType, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """處理代理人管理請求"""
        user_prompt = input_data.get('user_prompt', '')
        
        try:
            if intent == IntentType.AGENT_CREATION:
                return await self._handle_agent_creation(user_prompt, input_data)
            elif intent == IntentType.AGENT_DELETION:
                return await self._handle_agent_deletion(user_prompt)
            elif intent == IntentType.AGENT_QUERY:
                return await self._handle_agent_query()
            else:
                return {"status": "ERROR", "message": "未知的代理人管理請求"}
                
        except Exception as e:
            logger.error(f"處理代理人管理請求失敗: {e}")
            return {"status": "ERROR", "message": f"處理失敗: {str(e)}"}
    
    async def _handle_agent_creation(self, user_prompt: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """處理代理人創建請求"""
        # 分析用戶需求並生成代理人規格
        agent_spec = self._analyze_agent_requirements(user_prompt)
        
        return {
            "status": "PLANNING",
            "message": "代理人創建計劃已生成，請確認後執行",
            "agent_spec": agent_spec,
            "confirmation_required": True
        }
    
    async def _handle_agent_deletion(self, user_prompt: str) -> Dict[str, Any]:
        """處理代理人刪除請求"""
        # 從用戶輸入中提取要刪除的代理人ID
        agent_id = self._extract_agent_id_from_prompt(user_prompt)
        
        if not agent_id:
            available_agents = await self.communication_service.get_available_agents()
            return {
                "status": "INFO",
                "message": "請指定要刪除的代理人ID",
                "available_agents": available_agents
            }
        
        return {
            "status": "CONFIRMATION_REQUIRED",
            "message": f"確認要刪除代理人 {agent_id} 嗎？這將移除所有相關資源。",
            "agent_id": agent_id,
            "action": "delete_agent"
        }
    
    async def _handle_agent_query(self) -> Dict[str, Any]:
        """處理代理人查詢請求"""
        available_agents = await self.communication_service.get_available_agents()
        
        return {
            "status": "SUCCESS",
            "message": "目前可用的代理人列表",
            "agents": available_agents
        }
    
    async def execute_agent_creation(self, agent_spec: Dict[str, Any]) -> Dict[str, Any]:
        """執行代理人創建（用戶確認後）"""
        try:
            # 創建 AgentInfo 對象
            agent_info = AgentInfo(
                agent_id=agent_spec["agent_id"],
                agent_type=agent_spec["agent_type"],
                role=agent_spec["role"],
                goal=agent_spec["goal"],
                backstory=agent_spec["backstory"],
                capabilities=agent_spec.get("capabilities", []),
                status="CREATING"
            )
            
            # 保存到資料庫
            await self._save_agent_to_database(agent_info)
            
            # 創建資源
            result = await self.deployment_service.create_agent_resources(agent_info)
            
            if result["status"] == "SUCCESS":
                # 廣播新代理人註冊
                await self.communication_service.broadcast_agent_registry_update(
                    "AGENT_ADDED", agent_info.dict()
                )
            
            return result
            
        except Exception as e:
            logger.error(f"執行代理人創建失敗: {e}")
            return {"status": "ERROR", "error": str(e)}
    
    async def execute_agent_deletion(self, agent_id: str) -> Dict[str, Any]:
        """執行代理人刪除（用戶確認後）"""
        try:
            result = await self.deployment_service.delete_agent_resources(agent_id)
            return result
            
        except Exception as e:
            logger.error(f"執行代理人刪除失敗: {e}")
            return {"status": "ERROR", "error": str(e)}
    
    async def forward_task_to_suitable_agent(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """將任務轉發給合適的代理人"""
        try:
            task_description = task_data.get("user_prompt", "")
            required_capabilities = task_data.get("required_capabilities", [])
            
            # 找到合適的代理人
            suitable_agent = await self.communication_service.find_suitable_agent(
                task_description, required_capabilities
            )
            
            if not suitable_agent:
                return {
                    "status": "ERROR",
                    "message": "找不到合適的代理人處理此任務"
                }
            
            # 轉發任務
            result = await self.communication_service.forward_task_to_agent(
                suitable_agent["agent_id"], task_data, "orchestrator-agent"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"任務轉發失敗: {e}")
            return {"status": "ERROR", "error": str(e)}
    
    def _analyze_agent_requirements(self, user_prompt: str) -> Dict[str, Any]:
        """分析用戶需求並生成代理人規格"""
        # 基於用戶輸入生成代理人規格
        prompt_lower = user_prompt.lower()
        
        # 預設規格
        agent_spec = {
            "agent_id": f"custom-agent-{int(time.time())}",
            "agent_type": "omni_agent",
            "role": "通用助手",
            "goal": "協助用戶完成各種任務",
            "backstory": "你是一個靈活的AI助手，能夠適應各種不同的任務需求。",
            "capabilities": ["general_assistance"]
        }
        
        # 根據關鍵字調整規格
        import time
        if any(keyword in prompt_lower for keyword in ["技術", "程式", "開發", "架構"]):
            agent_spec.update({
                "agent_id": f"tech-specialist-{int(time.time())}",
                "role": "技術專家",
                "goal": "提供技術分析和開發建議",
                "backstory": "你是一位經驗豐富的技術專家，專精於軟體開發和系統架構。",
                "capabilities": ["technical_analysis", "code_review", "architecture_design"]
            })
        elif any(keyword in prompt_lower for keyword in ["設計", "美觀", "風格", "ui"]):
            agent_spec.update({
                "agent_id": f"design-specialist-{int(time.time())}",
                "role": "設計專家",
                "goal": "提供設計建議和美學指導",
                "backstory": "你是一位創意設計專家，擅長UI/UX設計和視覺美學。",
                "capabilities": ["ui_design", "visual_design", "user_experience"]
            })
        
        return agent_spec
    
    def _extract_agent_id_from_prompt(self, user_prompt: str) -> Optional[str]:
        """從用戶輸入中提取代理人ID"""
        # 簡單的正則匹配，實際應用中可能需要更複雜的NLP
        import re
        
        # 尋找類似 "agent-id" 或 "代理人ID" 的模式
        patterns = [
            r'([a-zA-Z0-9-]+(?:agent|specialist)[a-zA-Z0-9-]*)',
            r'ID[：:]\s*([a-zA-Z0-9-]+)',
            r'代理人[：:]\s*([a-zA-Z0-9-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_prompt, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    async def _save_agent_to_database(self, agent_info: AgentInfo):
        """保存代理人資訊到資料庫"""
        from google.cloud import firestore
        
        agent_data = agent_info.dict()
        agent_data["created_at"] = firestore.SERVER_TIMESTAMP
        agent_data["updated_at"] = firestore.SERVER_TIMESTAMP
        
        self.db.collection("agents").document(agent_info.agent_id).set(agent_data)
    
    def determine_delegation_target(self, intent: IntentType) -> str:
        """根據意圖決定委派目標"""
        mapping = {
            IntentType.STYLE_ADVICE: "stylist-agent",
            IntentType.TECHNICAL_ANALYSIS: "tech-analyst-agent"
        }
        return mapping.get(intent, "proxy-agent")
    
    def generate_delegation_response(self, intent: IntentType, user_prompt: str) -> str:
        """生成委派時的回應"""
        if intent == IntentType.STYLE_ADVICE:
            return "好的，我已將您的造型需求轉告給專業造型師，請稍候片刻！"
        elif intent == IntentType.TECHNICAL_ANALYSIS:
            return "收到您的技術分析請求，我已轉交給技術專家進行分析，請稍等。"
        else:
            return "我已將您的需求轉交給相關專家處理，請稍候。"

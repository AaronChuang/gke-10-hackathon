from crewai import Agent, Task
from typing import Dict, Any, Optional

from .base import BaseAgentWrapper


class OmniAgent(BaseAgentWrapper):
    """全能代理人 - 可配置角色和目標的通用代理人"""
    
    def __init__(self, task_id: str = None, output_field: str = None, 
                 custom_role: str = None, custom_goal: str = None, custom_backstory: str = None):
        super().__init__("omni-agent", task_id, output_field)
        self.custom_role = custom_role
        self.custom_goal = custom_goal
        self.custom_backstory = custom_backstory
    
    def create_agent(self) -> Agent:
        """創建可配置的全能代理人實例"""
        # 使用外部參數或預設值
        role = self.custom_role or "全能智慧助手"
        goal = self.custom_goal or "根據用戶需求提供專業、準確的協助和建議"
        backstory = self.custom_backstory or """你是一個高度適應性的智慧助手，能夠根據不同的情境和需求調整你的專業知識和回應風格。
        你擁有廣泛的知識基礎，能夠處理各種類型的查詢和任務。
        你的所有回答都嚴格基於提供的上下文資訊，絕不捏造任何內容。
        當上下文中沒有相關資訊時，你會誠實地告知用戶你不知道。
        請保持回應專業、準確且有用。"""
        
        return Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            llm=self.llm,
            allow_delegation=False,
            verbose=True
        )
    
    def create_task(self, input_data: Dict[str, Any]) -> Task:
        """創建全能任務"""
        user_prompt = input_data.get('user_prompt', '')
        conversation_history = input_data.get('conversation_history', [])
        product_context = input_data.get('product_context', {})
        custom_instructions = input_data.get('custom_instructions', '')
        
        # 構建上下文
        context_parts = [f"用戶請求：{user_prompt}"]
        
        if conversation_history:
            context_parts.append("\n對話歷史：")
            for msg in conversation_history[-5:]:  # 保留更多歷史以提供更好的上下文
                sender = "用戶" if msg.get("sender") == "user" else "AI"
                context_parts.append(f"{sender}: {msg.get('text', '')}")
        
        if product_context:
            context_parts.append(f"\n相關商品資訊：{product_context.get('name', '')} - {product_context.get('description', '')}")
        
        if custom_instructions:
            context_parts.append(f"\n特殊指示：{custom_instructions}")
        
        context = "\n".join(context_parts)
        
        return Task(
            description=f"""
            請基於以下上下文和你的角色設定，為用戶提供最佳的協助：

            {context}

            請根據你的角色和目標，提供準確、專業且有用的回應。
            確保所有回答都基於提供的上下文資訊。
            如果需要額外資訊才能完整回答，請明確說明需要什麼資訊。
            """,
            expected_output="基於角色設定和上下文的專業回應",
            agent=self.agent
        )
    
    def update_configuration(self, role: str = None, goal: str = None, backstory: str = None):
        """動態更新代理人配置"""
        if role:
            self.custom_role = role
        if goal:
            self.custom_goal = goal
        if backstory:
            self.custom_backstory = backstory
        
        # 重新創建 agent 以應用新配置
        self.agent = self.create_agent()
    
    def get_current_configuration(self) -> Dict[str, str]:
        """獲取當前配置"""
        return {
            "role": self.custom_role or "全能智慧助手",
            "goal": self.custom_goal or "根據用戶需求提供專業、準確的協助和建議",
            "backstory": self.custom_backstory or "預設背景故事"
        }

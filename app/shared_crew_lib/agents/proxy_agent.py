from crewai import Agent, Task
from typing import Dict, Any, Tuple, List, Optional
import re

from .base import BaseAgentWrapper


class ProxyAgent(BaseAgentWrapper):
    """代理代理人 - 處理一般性任務和轉發請求"""
    
    def __init__(self, task_id: str = None, output_field: str = None):
        super().__init__("proxy-agent", task_id, output_field)
    
    def create_agent(self) -> Agent:
        """創建代理代理人實例"""
        return Agent(
            role="通用任務代理人",
            goal="處理一般性查詢和協助用戶解決基本問題",
            backstory="""你是一個多才多藝的通用助手，能夠處理各種基本查詢和任務。
            你擅長提供準確的資訊、回答常見問題，並在必要時引導用戶到合適的專業服務。
            你的回答總是基於提供的上下文，絕不捏造資訊。
            當遇到超出你能力範圍的專業問題時，你會誠實地說明並建議尋求專業協助。
            請保持回應友善、專業且簡潔明確。""",
            llm=self.llm,
            allow_delegation=False,
            verbose=True
        )
    
    def create_task(self, input_data: Dict[str, Any]) -> Task:
        """創建代理任務"""
        user_prompt = input_data.get('user_prompt', '')
        conversation_history = input_data.get('conversation_history', [])
        product_context = input_data.get('product_context', {})
        
        # 構建上下文
        context_parts = [f"用戶查詢：{user_prompt}"]
        
        if conversation_history:
            context_parts.append("\n對話歷史：")
            for msg in conversation_history[-3:]:
                sender = "用戶" if msg.get("sender") == "user" else "AI"
                context_parts.append(f"{sender}: {msg.get('text', '')}")
        
        if product_context:
            context_parts.append(f"\n相關商品：{product_context.get('name', '')} - {product_context.get('description', '')}")
        
        context = "\n".join(context_parts)
        
        return Task(
            description=f"""
            請基於以下上下文回答用戶的查詢：

            {context}

            請提供準確、有用的回應。如果問題超出你的專業範圍，請誠實說明並建議用戶尋求相關專業協助。
            回答要友善、專業且簡潔明確。
            """,
            expected_output="基於上下文的準確回應",
            agent=self.agent
        )
    
    def should_forward_task(self, user_prompt: str) -> Tuple[bool, Optional[str], List[str]]:
        """
        判斷是否需要轉發任務給其他代理人
        
        Returns:
            Tuple[bool, Optional[str], List[str]]: (是否需要轉發, 目標代理人, 所需能力)
        """
        user_prompt_lower = user_prompt.lower()
        
        # 技術分析相關關鍵詞
        tech_keywords = [
            '技術分析', '股票分析', '財務報表', '投資建議', '市場趨勢',
            '股價', '財報', '營收', '獲利', '股利', '本益比', 'pe ratio',
            'technical analysis', 'stock', 'financial', 'investment'
        ]
        
        # 造型建議相關關鍵詞
        style_keywords = [
            '造型', '搭配', '穿搭', '時尚', '服裝', '配色', '風格',
            '髮型', '妝容', '配件', '鞋子', '包包', '飾品',
            'style', 'fashion', 'outfit', 'clothing', 'makeup', 'hair'
        ]
        
        # 檢查是否包含技術分析關鍵詞
        if any(keyword in user_prompt_lower for keyword in tech_keywords):
            return True, "tech-analyst-agent", ["financial_analysis", "technical_analysis", "market_research"]
        
        # 檢查是否包含造型建議關鍵詞
        if any(keyword in user_prompt_lower for keyword in style_keywords):
            return True, "stylist-agent", ["fashion_advice", "style_consultation", "color_matching"]
        
        # 檢查複雜問題模式
        complex_patterns = [
            r'如何.*分析.*',
            r'請.*建議.*策略',
            r'專業.*意見',
            r'深入.*研究',
            r'詳細.*報告'
        ]
        
        for pattern in complex_patterns:
            if re.search(pattern, user_prompt):
                # 根據上下文判斷需要哪種專業能力
                if any(keyword in user_prompt_lower for keyword in tech_keywords):
                    return True, "tech-analyst-agent", ["financial_analysis", "research"]
                elif any(keyword in user_prompt_lower for keyword in style_keywords):
                    return True, "stylist-agent", ["fashion_advice", "consultation"]
                else:
                    # 通用複雜問題，需要找合適的代理人
                    return True, None, ["analysis", "consultation", "research"]
        
        # 一般問題，不需要轉發
        return False, None, []
    
    def analyze_user_intent(self, user_prompt: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        分析用戶意圖和需求
        
        Returns:
            Dict包含: intent_type, confidence, suggested_agent, reasoning
        """
        should_forward, target_agent, capabilities = self.should_forward_task(user_prompt)
        
        if should_forward:
            if target_agent:
                return {
                    "intent_type": "specialized_query",
                    "confidence": 0.8,
                    "suggested_agent": target_agent,
                    "required_capabilities": capabilities,
                    "reasoning": f"用戶查詢需要 {target_agent} 的專業能力"
                }
            else:
                return {
                    "intent_type": "complex_query",
                    "confidence": 0.6,
                    "suggested_agent": None,
                    "required_capabilities": capabilities,
                    "reasoning": "複雜查詢需要專業代理人處理"
                }
        else:
            return {
                "intent_type": "general_query",
                "confidence": 0.9,
                "suggested_agent": "proxy-agent",
                "required_capabilities": ["general_assistance"],
                "reasoning": "一般性查詢可由代理人直接處理"
            }

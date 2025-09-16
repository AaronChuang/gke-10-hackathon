from pydantic import BaseModel, Field
from typing import Dict, Any

class AgentTaskMessage(BaseModel):
    """
    定義在 Pub/Sub 主題之間傳遞的訊息結構。
    """
    task_id: str = Field(..., description="在 Firestore 中的唯一任務 ID")
    input_data: Dict[str, Any] = Field(..., description="傳遞給 Agent 的輸入數據")
    history: str = Field("", description="前一個 Agent 的執行結果或歷史紀錄")

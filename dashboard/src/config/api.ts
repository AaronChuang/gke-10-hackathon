// API 配置
export const API_CONFIG = {
  // Orchestrator API (端口 8000)
  ORCHESTRATOR_BASE_URL: 'http://localhost:8000',
  
  // Proxy Agent API (端口 8001) 
  PROXY_AGENT_BASE_URL: 'http://localhost:8001',
  
  // API 端點
  ENDPOINTS: {
    // Orchestrator 端點
    AGENTS: '/api/agents',
    KNOWLEDGE_BASE: '/api/knowledge-base',
    START_TASK: '/api/start-task',
    
    // Proxy Agent 端點
    CONVERSATION: '/api/conversation',
  }
}

// 獲取完整的 API URL
export const getApiUrl = (endpoint: keyof typeof API_CONFIG.ENDPOINTS): string => {
  const path = API_CONFIG.ENDPOINTS[endpoint]
  
  // 根據端點決定使用哪個服務
  if (endpoint === 'CONVERSATION') {
    return `${API_CONFIG.PROXY_AGENT_BASE_URL}${path}`
  } else {
    return `${API_CONFIG.ORCHESTRATOR_BASE_URL}${path}`
  }
}

// 便捷方法
export const API_URLS = {
  CONVERSATION: getApiUrl('CONVERSATION'),
  AGENTS: getApiUrl('AGENTS'),
  KNOWLEDGE_BASE: getApiUrl('KNOWLEDGE_BASE'),
  START_TASK: getApiUrl('START_TASK'),
}

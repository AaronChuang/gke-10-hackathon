export interface Task {
  task_id: string
  status: TaskStatus
  initial_prompt: string
  created_at: number
  tech_analyst_started_at?: number
  architect_started_at?: number
  stylist_started_at?: number
  completed_at?: number
  tech_analyst_output?: string
  architect_output?: string
  stylist_output?: string
  error_source?: string
  error_message?: string
  user_id?: string
  initial_request?: any
  conversation_history?: ConversationMessage[]
  product_context?: any
  agent_history?: AgentHistoryEntry[]
  total_tokens?: TokenUsage
  log?: TaskLogEntry[]
}

export interface ConversationMessage {
  sender: 'user' | 'ai'
  text: string
  timestamp?: number
}

export interface AgentHistoryEntry {
  agent_name: string
  started_at: number
  completed_at?: number
  status: 'RUNNING' | 'COMPLETED' | 'FAILED'
  input_tokens: number
  output_tokens: number
  error_message?: string
}

export interface TokenUsage {
  input_tokens: number
  output_tokens: number
  total_cost_usd?: number
}

export interface TaskLogEntry {
  timestamp: number
  level: 'INFO' | 'WARNING' | 'ERROR'
  message: string
  agent_name?: string
  metadata?: Record<string, any>
}

export type TaskStatus = 
  | 'PENDING'
  | 'RUNNING'
  | 'TECH_ANALYST_RUNNING'
  | 'ARCHITECT_PENDING'
  | 'ARCHITECT_RUNNING'
  | 'STYLIST_RUNNING'
  | 'COMPLETED'
  | 'FAILED'

export interface TaskTableRow {
  id: string
  status: TaskStatus
  prompt: string
  createdAt: string
  isRunning: boolean
  totalTokens?: number
  agentCount?: number
  lastAgent?: string
  errorMessage?: string
}

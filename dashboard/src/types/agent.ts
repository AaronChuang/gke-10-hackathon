export interface Agent {
  agent_id: string
  name: string
  description: string
  system_prompt: string
  status: AgentStatus
  pubsub_topic: string
  capabilities: string[]
  created_at: number
  updated_at: number
}

export type AgentStatus = 
  | 'ACTIVE'
  | 'INACTIVE' 
  | 'CREATING'
  | 'FAILED'

export interface CreateAgentRequest {
  name: string
  description: string
  system_prompt: string
  capabilities: string[]
  pubsub_topic?: string
}

export interface UpdateAgentRequest {
  name?: string
  description?: string
  system_prompt?: string
  capabilities?: string[]
  status?: AgentStatus
}

export interface AgentTableRow {
  id: string
  name: string
  description: string
  status: AgentStatus
  capabilities: string[]
  createdAt: string
  isActive: boolean
}

import { ref, onUnmounted } from 'vue'
import { 
  collection, 
  query, 
  orderBy, 
  onSnapshot, 
  type Unsubscribe 
} from 'firebase/firestore'
import type { Agent, CreateAgentRequest } from '../types/agent'

export function useAgents() {
  const agents = ref<Agent[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  let unsubscribe: Unsubscribe | null = null
  let db: any = null

  const loadAgents = async () => {
    // 如果已經有監聽器在運行，就不需要重新設置
    if (unsubscribe) {
      return
    }
    
    loading.value = true
    error.value = null
    
    try {
      if (!db) {
        const { getFirestore } = await import('firebase/firestore')
        const { initializeApp } = await import('firebase/app')
        const firebaseConfig = {
          apiKey: "AIzaSyBQ8lOT39SnvFqlnnch9G_W8wa0jlfUg5E",
          authDomain: "gke-10-hackathon-471902.firebaseapp.com",
          projectId: "gke-10-hackathon-471902",
          storageBucket: "gke-10-hackathon-471902.firebasestorage.app",
          messagingSenderId: "679895434316",
          appId: "1:679895434316:web:9d1183ab38f168d24060e9"
        }
        const app = initializeApp(firebaseConfig)
        db = getFirestore(app, "gke-10-hackathon")
      }

      const agentsCollection = collection(db, 'agents')
      const q = query(agentsCollection, orderBy('created_at', 'desc'))
      
      console.log('Setting up real-time listener for agents collection...')
      
      unsubscribe = onSnapshot(q,
        (querySnapshot) => {
          console.log(`Received ${querySnapshot.size} agents from Firebase`)
          const agentList: Agent[] = []

          querySnapshot.forEach((doc) => {
            const data = doc.data()
            const agent: Agent = {
              agent_id: doc.id,
              name: data.name || '',
              description: data.description || '',
              system_prompt: data.system_prompt || '',
              status: data.status || 'INACTIVE',
              pubsub_topic: data.pubsub_topic || '',
              capabilities: data.capabilities || [],
              created_at: data.created_at || 0,
              updated_at: data.updated_at || 0
            }
            agentList.push(agent)
          })
          
          agents.value = agentList
          loading.value = false
          error.value = null
        },
        (err) => {
          console.error('Agents snapshot error:', err)
          error.value = `無法載入代理人資料: ${err.message}`
          loading.value = false
        }
      )
    } catch (err) {
      console.error('Load agents error:', err)
      error.value = '載入代理人資料失敗'
      loading.value = false
    }
  }

  const createAgent = async (agentData: CreateAgentRequest): Promise<boolean> => {
    try {
      const response = await fetch('/api/agents', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(agentData)
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '創建代理人失敗')
      }
      
      return true
    } catch (err) {
      console.error('Create agent error:', err)
      error.value = `創建代理人失敗: ${err}`
      return false
    }
  }

  const updateAgent = async (agentId: string, updates: Partial<Agent>): Promise<boolean> => {
    try {
      const response = await fetch(`/api/agents/${agentId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates)
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '更新代理人失敗')
      }
      
      return true
    } catch (err) {
      console.error('Update agent error:', err)
      error.value = `更新代理人失敗: ${err}`
      return false
    }
  }

  const deleteAgent = async (agentId: string): Promise<boolean> => {
    try {
      // 不允許刪除 OrchestratorAgent
      const agent = agents.value.find((a: Agent) => a.agent_id === agentId)
      if (agent?.name === 'OrchestratorAgent') {
        error.value = '無法刪除系統核心代理人'
        return false
      }
      
      const response = await fetch(`/api/agents/${agentId}`, {
        method: 'DELETE'
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '刪除代理人失敗')
      }
      
      return true
    } catch (err) {
      console.error('Delete agent error:', err)
      error.value = `刪除代理人失敗: ${err}`
      return false
    }
  }

  const cleanup = () => {
    if (unsubscribe) {
      unsubscribe()
      unsubscribe = null
    }
  }

  onUnmounted(() => {
    cleanup()
  })

  return {
    agents,
    loading,
    error,
    loadAgents,
    createAgent,
    updateAgent,
    deleteAgent,
    cleanup
  }
}

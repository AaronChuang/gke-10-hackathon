import { ref, onUnmounted } from 'vue'
import { 
  getFirestore, 
  collection, 
  query, 
  orderBy, 
  onSnapshot,
  type Unsubscribe 
} from 'firebase/firestore'

export interface ConversationMessage {
  content: string
  sender: string
  timestamp: number
}

export interface Conversation {
  session_id: string
  context?: {
    user_id?: string
  }
  messages?: ConversationMessage[]
  summary?: {
    total_messages: number
  }
  updated_at: number
  totalTokens?: number
}

export function useConversations() {
  const conversations = ref<Conversation[]>([])
  const loading = ref(true)
  const error = ref<string | null>(null)
  
  let unsubscribe: Unsubscribe | null = null

  const loadConversations = async () => {
    try {
      // Get Firestore instance (assuming Firebase is already initialized)
      const db = getFirestore()
      
      console.log("Loading conversations from Firebase...")
      
      // Try to read from conversations collection
      try {
        const conversationsCollection = collection(db, 'conversations')
        const q = query(conversationsCollection, orderBy('updated_at', 'desc'))
        
        // Set up real-time listener
        unsubscribe = onSnapshot(q,
          (querySnapshot) => {
            console.log(`Received ${querySnapshot.size} conversations from listener`)
            const conversationList: Conversation[] = []

            querySnapshot.forEach((doc) => {
              const data = doc.data()
              const conversation: Conversation = {
                session_id: doc.id,
                context: data.context || {},
                messages: data.messages || [],
                summary: data.summary || { total_messages: 0 },
                updated_at: data.updated_at || 0,
                totalTokens: data.totalTokens || 0
              }
              conversationList.push(conversation)
            })
            
            console.log("Updated conversation list:", conversationList.length, "conversations")
            conversations.value = conversationList
            loading.value = false
            error.value = null
          },
          (err) => {
            console.error('Firebase conversations snapshot error:', err)
            error.value = `Unable to load conversations: ${err.message}`
            loading.value = false
          }
        )
      } catch (readError) {
        console.warn("Failed to read conversations collection:", readError)
        // If collection doesn't exist or is empty, set empty array
        conversations.value = []
        loading.value = false
        error.value = null
      }
    } catch (err) {
      console.error('Conversations loading error:', err)
      error.value = 'Failed to load conversations'
      loading.value = false
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
    conversations,
    loading,
    error,
    loadConversations,
    cleanup
  }
}

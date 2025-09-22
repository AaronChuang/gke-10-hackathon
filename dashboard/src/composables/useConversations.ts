import { ref, onUnmounted } from 'vue'
import { 
  collection, 
  query, 
  orderBy, 
  onSnapshot,
  type Unsubscribe 
} from 'firebase/firestore'

export interface ConversationMessage {
  message_id: string
  content: string
  sender: string
  timestamp: number
  metadata?: Record<string, any>
}

export interface ConversationContext {
  user_id?: string
  session_type?: string
  language?: string
  preferences?: Record<string, any>
  product_context?: Record<string, any>
}

export interface ConversationSummary {
  total_messages: number
  user_messages: number
  ai_messages: number
  topics?: string[]
  key_points?: string[]
  sentiment?: string
}

export interface Conversation {
  session_id: string
  status: string
  context: ConversationContext
  messages: ConversationMessage[]
  created_at: number
  updated_at: number
  last_activity_at: number
  summary: ConversationSummary
  related_tasks?: string[]
  metadata?: Record<string, any>
}

export function useConversations() {
  const conversations = ref<Conversation[]>([])
  const loading = ref(true)
  const error = ref<string | null>(null)
  
  let unsubscribe: Unsubscribe | null = null
  let db: any = null

  const loadConversations = async () => {
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

      console.log("Loading conversations from Firebase...")
      
      const conversationsCollection = collection(db, 'conversations')
      const q = query(conversationsCollection, orderBy('updated_at', 'desc'))
      
      console.log('Setting up real-time listener for conversations collection...')
      
      unsubscribe = onSnapshot(q,
        (querySnapshot) => {
          console.log(`Received ${querySnapshot.size} conversations from Firebase`)
          const conversationList: Conversation[] = []

          querySnapshot.forEach((doc) => {
            const data = doc.data()
            const conversation: Conversation = {
              session_id: doc.id,
              status: data.status || 'active',
              context: data.context || {},
              messages: data.messages || [],
              created_at: data.created_at || 0,
              updated_at: data.updated_at || 0,
              last_activity_at: data.last_activity_at || 0,
              summary: data.summary || { 
                total_messages: 0, 
                user_messages: 0, 
                ai_messages: 0 
              },
              related_tasks: data.related_tasks || [],
              metadata: data.metadata || {}
            }
            conversationList.push(conversation)
          })
          
          conversations.value = conversationList
          loading.value = false
          error.value = null
        },
        (err) => {
          console.error('Conversations snapshot error:', err)
          error.value = `無法載入對話資料: ${err.message}`
          loading.value = false
        }
      )
    } catch (err) {
      console.error('Load conversations error:', err)
      error.value = '載入對話資料失敗'
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

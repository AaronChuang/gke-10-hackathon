import { ref, onUnmounted } from 'vue'
import { 
  collection, 
  query, 
  orderBy, 
  onSnapshot, 
  type Unsubscribe 
} from 'firebase/firestore'
import type { KnowledgeEntry, IndexWebsiteRequest } from '../types/knowledge'
import { API_URLS } from '@/config/api'

export function useKnowledgeBase() {
  const knowledgeEntries = ref<KnowledgeEntry[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  let unsubscribe: Unsubscribe | null = null
  let db: any = null

  const loadKnowledgeBase = async () => {
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

      const kbCollection = collection(db, 'knowledge_base')
      const q = query(kbCollection, orderBy('created_at', 'desc'))
      
      console.log('Setting up real-time listener for knowledge_base collection...')
      
      unsubscribe = onSnapshot(q,
        (querySnapshot) => {
          console.log(`Received ${querySnapshot.size} knowledge entries from Firebase`)
          const kbList: KnowledgeEntry[] = []

          querySnapshot.forEach((doc) => {
            const data = doc.data()
            const entry: KnowledgeEntry = {
              kb_id: doc.id,
              url: data.url || '',
              status: data.status || 'QUEUED',
              created_at: data.created_at || 0,
              updated_at: data.updated_at || 0,
              indexed_pages: data.indexed_pages || 0,
              total_pages: data.total_pages || 0,
              error_message: data.error_message || null,
              metadata: data.metadata || {}
            }
            kbList.push(entry)
          })
          
          knowledgeEntries.value = kbList
          loading.value = false
          error.value = null
        },
        (err) => {
          console.error('Knowledge base snapshot error:', err)
          error.value = `無法載入知識庫資料: ${err.message}`
          loading.value = false
        }
      )
    } catch (err) {
      console.error('Load knowledge base error:', err)
      error.value = '載入知識庫資料失敗'
      loading.value = false
    }
  }

  const indexWebsite = async (request: IndexWebsiteRequest): Promise<boolean> => {
    try {
      // 調用後端 API 來索引網站
      const response = await fetch(`${API_URLS.KNOWLEDGE_BASE}/index`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request)
      })

      if (!response.ok) {
        const errorData = await response.json()
        error.value = errorData.detail || '索引網站失敗'
        return false
      }

      return true
    } catch (err) {
      console.error('Index website error:', err)
      error.value = `索引網站失敗: ${err}`
      return false
    }
  }

  const deleteKnowledgeEntry = async (kbId: string): Promise<boolean> => {
    try {
      const response = await fetch(`${API_URLS.KNOWLEDGE_BASE}/${kbId}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        const errorData = await response.json()
        error.value = errorData.detail || '刪除知識庫項目失敗'
        return false
      }

      return true
    } catch (err) {
      console.error('Delete knowledge entry error:', err)
      error.value = `刪除知識庫項目失敗: ${err}`
      return false
    }
  }

  const reindexWebsite = async (kbId: string): Promise<boolean> => {
    try {
      const response = await fetch(`${API_URLS.KNOWLEDGE_BASE}/reindex/${kbId}`, {
        method: 'POST'
      })

      if (!response.ok) {
        const errorData = await response.json()
        error.value = errorData.detail || '重新索引失敗'
        return false
      }

      return true
    } catch (err) {
      console.error('Reindex website error:', err)
      error.value = `重新索引失敗: ${err}`
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
    knowledgeEntries,
    loading,
    error,
    loadKnowledgeBase,
    indexWebsite,
    deleteKnowledgeEntry,
    reindexWebsite,
    cleanup
  }
}

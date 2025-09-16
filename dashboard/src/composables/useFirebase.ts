import { ref, onUnmounted } from 'vue'
import { initializeApp } from 'firebase/app'
import { 
  getFirestore, 
  collection, 
  query, 
  orderBy, 
  onSnapshot, 
  getDocs,
  type Unsubscribe 
} from 'firebase/firestore'
import type { Task } from '@/types/task'

const firebaseConfig = {
  apiKey: "AIzaSyBQ8lOT39SnvFqlnnch9G_W8wa0jlfUg5E",
  authDomain: "gke-10-hackathon-471902.firebaseapp.com",
  projectId: "gke-10-hackathon-471902",
  storageBucket: "gke-10-hackathon-471902.firebasestorage.app",
  messagingSenderId: "679895434316",
  appId: "1:679895434316:web:9d1183ab38f168d24060e9"
}

export function useFirebase() {
  const tasks = ref<Task[]>([])
  const loading = ref(true)
  const error = ref<string | null>(null)
  
  let unsubscribe: Unsubscribe | null = null

  const initFirebase = async () => {
    try {
      const app = initializeApp(firebaseConfig)
      console.log("Firebase app initialized:", app.name)
      
      const db = getFirestore(app, "gke-10-hackathon")
      console.log("Firestore database connected")

      // 先測試一次性讀取，確認連接正常
      try {
        const testSnapshot = await getDocs(collection(db, "tasks"))
        console.log(`Found ${testSnapshot.size} tasks in collection`)
        
        testSnapshot.forEach((doc) => {
          console.log("Task:", doc.id, "=>", doc.data())
        })
      } catch (testError) {
        console.warn("Test read failed, but continuing with listener:", testError)
      }

      // 設置即時監聽
      const tasksCollection = collection(db, 'tasks')
      const q = query(tasksCollection, orderBy('created_at', 'desc'))
      
      console.log("Setting up real-time listener for tasks collection...")
      
      unsubscribe = onSnapshot(q,
        (querySnapshot) => {
          console.log(`Received ${querySnapshot.size} tasks from listener`)
          const taskList: Task[] = []

          querySnapshot.forEach((doc) => {
            const data = doc.data()
            const task: Task = {
              task_id: doc.id,
              status: data.status || 'PENDING',
              initial_prompt: data.initial_prompt || '',
              created_at: data.created_at || 0,
              tech_analyst_started_at: data.tech_analyst_started_at,
              architect_started_at: data.architect_started_at,
              stylist_started_at: data.stylist_started_at,
              completed_at: data.completed_at,
              tech_analyst_output: data.tech_analyst_output,
              architect_output: data.architect_output,
              stylist_output: data.stylist_output,
              error_source: data.error_source,
              error_message: data.error_message,
              // 新增的欄位
              user_id: data.user_id,
              initial_request: data.initial_request,
              conversation_history: data.conversation_history || [],
              product_context: data.product_context,
              agent_history: data.agent_history || [],
              total_tokens: data.total_tokens || 0,
              log: data.log || []
            }
            taskList.push(task)
          })
          
          console.log("Updated task list:", taskList.length, "tasks")
          tasks.value = taskList
          loading.value = false
          error.value = null
        },
        (err) => {
          console.error('Firebase snapshot error:', err)
          error.value = `無法連接到 Firebase: ${err.message}`
          loading.value = false
        }
      )
    } catch (err) {
      console.error('Firebase initialization error:', err)
      error.value = 'Firebase 初始化失敗'
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
    tasks,
    loading,
    error,
    initFirebase,
    cleanup
  }
}

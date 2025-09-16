<template>
  <div id="app" class="app-container">
    <header class="app-header">
      <h1 class="text-3xl font-bold text-gray-800 mb-2">
        <i class="fas fa-brain mr-3 text-blue-600"></i>
        AI Agent Dashboard
      </h1>
      <p class="text-gray-600">智能代理人協調與監控中心</p>
      
    </header>

    <nav class="tab-navigation">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        :class="['tab-button', { active: activeTab === tab.id }]"
        @click="activeTab = tab.id"
      >
        <i :class="tab.icon"></i>
        {{ tab.name }}
      </button>
    </nav>

    <main class="app-main">
      <LoadingSpinner 
        v-if="loading" 
        :message="loadingMessage"
      />
      
      <ErrorMessage 
        v-else-if="error" 
        :message="error"
        @retry="initFirebase"
      />
      
      <div v-else class="tab-content">
        <!-- 任務儀表板 -->
        <TaskDashboard 
          v-if="activeTab === 'tasks'"
          :tasks="tasks"
        />
        
        <!-- 代理人管理 -->
        <AgentManagement 
          v-else-if="activeTab === 'agents'"
          :agents="agents"
          @refresh="loadAgents"
        />
        
        <!-- 知識庫管理 -->
        <KnowledgeBase 
          v-else-if="activeTab === 'knowledge'"
          :knowledge-entries="knowledgeEntries"
          @refresh="loadKnowledgeBase"
        />
        
        <!-- 對話測試 -->
        <ChatTest 
          v-else-if="activeTab === 'chat'"
        />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useFirebase } from './composables/useFirebase'
import { useAgents } from './composables/useAgents'
import { useKnowledgeBase } from './composables/useKnowledgeBase'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import ErrorMessage from '@/components/ErrorMessage.vue'
import TaskDashboard from '@/components/TaskDashboard.vue'
import AgentManagement from '@/components/AgentManagement.vue'
import KnowledgeBase from '@/components/KnowledgeBase.vue'
import ChatTest from '@/components/ChatTest.vue'

const activeTab = ref('tasks')

const tabs = [
  { id: 'tasks', name: '任務儀表板', icon: 'fas fa-tasks' },
  { id: 'agents', name: '代理人管理', icon: 'fas fa-robot' },
  { id: 'knowledge', name: '知識庫管理', icon: 'fas fa-database' },
  { id: 'chat', name: '對話測試', icon: 'fas fa-comments' }
]

const { tasks, loading: tasksLoading, error: tasksError, initFirebase } = useFirebase()
const { agents, loading: agentsLoading, error: agentsError, loadAgents } = useAgents()
const { knowledgeEntries, loading: kbLoading, error: kbError, loadKnowledgeBase } = useKnowledgeBase()

const loading = computed(() => {
  switch (activeTab.value) {
    case 'tasks': return tasksLoading.value
    case 'agents': return agentsLoading.value
    case 'knowledge': return kbLoading.value
    case 'chat': return false
    default: return false
  }
})

const error = computed(() => {
  switch (activeTab.value) {
    case 'tasks': return tasksError.value
    case 'agents': return agentsError.value
    case 'knowledge': return kbError.value
    case 'chat': return null
    default: return null
  }
})

const loadingMessage = computed(() => {
  switch (activeTab.value) {
    case 'tasks': return '正在載入任務資料...'
    case 'agents': return '正在載入代理人資料...'
    case 'knowledge': return '正在載入知識庫資料...'
    case 'chat': return '正在初始化對話...'
    default: return '載入中...'
  }
})

onMounted(async () => {
  await initFirebase()
  await loadAgents()
  await loadKnowledgeBase()
})
</script>

<style lang="scss" scoped>
.app-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: $spacing-md;
  
  @media (min-width: 768px) {
    padding: $spacing-xl;
  }
}

.app-header {
  text-align: center;
  margin-bottom: $spacing-lg;
}

.app-title {
  font-size: 1.875rem;
  font-weight: 700;
  color: $text-primary;
  margin-bottom: $spacing-sm;
  
  @media (min-width: 768px) {
    font-size: 2.25rem;
  }
}

.app-subtitle {
  color: $text-muted;
  font-size: 1rem;
}

.tab-navigation {
  display: flex;
  justify-content: center;
  margin-bottom: $spacing-xl;
  border-bottom: 2px solid #e5e7eb;
  gap: $spacing-sm;
  
  @media (max-width: 768px) {
    flex-direction: column;
    gap: $spacing-xs;
  }
}

.tab-button {
  padding: $spacing-md $spacing-lg;
  border: none;
  background: transparent;
  color: $text-muted;
  font-weight: 500;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  
  &:hover {
    color: $text-primary;
    background-color: #f9fafb;
  }
  
  &.active {
    color: #3b82f6;
    border-bottom-color: #3b82f6;
    background-color: #eff6ff;
  }
  
  i {
    font-size: 1.1rem;
  }
  
  @media (max-width: 768px) {
    justify-content: center;
    border-bottom: none;
    border-radius: 8px;
    
    &.active {
      background-color: #3b82f6;
      color: white;
    }
  }
}

.app-main {
  min-height: 500px;
}

.tab-content {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

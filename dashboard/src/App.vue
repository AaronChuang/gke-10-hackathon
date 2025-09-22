<template>
  <div id="app" class="app-container">
    <header class="app-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="text-3xl font-bold text-gray-800 mb-2">
            <i class="fas fa-building mr-3 text-blue-600"></i>
            {{ $t('app.title') }}
          </h1>
          <p class="text-gray-600">{{ $t('app.subtitle') }}</p>
        </div>
        <LanguageSwitcher />
      </div>
    </header>

    <nav class="tab-navigation">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        :class="['tab-button', { active: activeTab === tab.id }]"
        @click="activeTab = tab.id"
      >
        <i :class="tab.icon"></i>
        {{ $t(`navigation.${tab.id}`) }}
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
        <StrategyConsultant 
          v-if="activeTab === 'strategy'"
        />
        
        <AgentManagement 
          v-else-if="activeTab === 'agents'"
          :agents="agents"
          @refresh="loadAgents"
        />
        
        <KnowledgeBase 
          v-else-if="activeTab === 'knowledge'"
        />
        
        <OperationsCenter 
          v-else-if="activeTab === 'operations'"
          :tasks="tasks"
        />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useFirebase } from './composables/useFirebase'
import { useAgents } from './composables/useAgents'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import ErrorMessage from '@/components/ErrorMessage.vue'
import StrategyConsultant from '@/components/StrategyConsultant.vue'
import AgentManagement from '@/components/AgentManagement.vue'
import KnowledgeBase from '@/components/KnowledgeBase.vue'
import OperationsCenter from '@/components/OperationsCenter.vue'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'

const { t } = useI18n()
const activeTab = ref('strategy')

const tabs = [
  { id: 'strategy', icon: 'fas fa-lightbulb' },
  { id: 'agents', icon: 'fas fa-users' },
  { id: 'knowledge', icon: 'fas fa-database' },
  { id: 'operations', icon: 'fas fa-chart-line' }
]

const { tasks, loading: tasksLoading, error: tasksError, initFirebase } = useFirebase()
const { agents, loading: agentsLoading, error: agentsError, loadAgents } = useAgents()

const loading = computed(() => {
  switch (activeTab.value) {
    case 'operations': return tasksLoading.value
    case 'agents': return agentsLoading.value
    case 'strategy': return false
    case 'knowledge': return false
    default: return false
  }
})

const error = computed(() => {
  switch (activeTab.value) {
    case 'operations': return tasksError.value
    case 'agents': return agentsError.value
    case 'strategy': return null
    case 'knowledge': return null
    default: return null
  }
})

const loadingMessage = computed(() => {
  switch (activeTab.value) {
    case 'operations': return t('loading.tasks')
    case 'agents': return t('loading.agents')
    case 'strategy': return t('loading.strategy')
    case 'knowledge': return t('loading.knowledge')
    default: return t('loading.default')
  }
})

onMounted(async () => {
  await initFirebase()
  await loadAgents()
})
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as *;

.app-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: $spacing-lg;
  background: $bg-primary;
  min-height: 100vh;
  
  @media (min-width: 768px) {
    padding: $spacing-xl;
  }
}

.app-header {
  margin-bottom: $spacing-2xl;
  
  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: $spacing-lg;
    
    @media (max-width: 768px) {
      flex-direction: column;
      align-items: center;
      text-align: center;
    }
  }
  
  .title-section {
    flex: 1;
    
    @media (max-width: 768px) {
      text-align: center;
    }
  }
  
  h1 {
    font-size: $font-4xl;
    font-weight: 700;
    color: $text-primary;
    margin-bottom: $spacing-md;
    display: flex;
    align-items: center;
    
    @media (max-width: 768px) {
      justify-content: center;
    }
    
    i {
      color: #3b82f6;
      margin-right: $spacing-md;
    }
    
    @media (min-width: 768px) {
      font-size: 3rem;
    }
  }
  
  p {
    color: $text-secondary;
    font-size: $font-lg;
    font-weight: 400;
  }
}

.tab-navigation {
  display: flex;
  justify-content: center;
  margin-bottom: $spacing-2xl;
  background: $bg-card;
  border-radius: 16px;
  padding: $spacing-sm;
  box-shadow: $shadow-lg;
  gap: $spacing-xs;
  
  @media (max-width: 768px) {
    flex-direction: column;
    gap: $spacing-xs;
  }
}

.tab-button {
  padding: $spacing-md $spacing-xl;
  border: none;
  background: transparent;
  color: $text-secondary;
  font-weight: 500;
  cursor: pointer;
  border-radius: 12px;
  transition: all $transition-normal;
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  font-size: $font-base;
  
  &:hover {
    color: $text-primary;
    background-color: $bg-hover;
    transform: translateY(-1px);
  }
  
  &.active {
    color: white;
    background: linear-gradient(135deg, #3b82f6, #1d4ed8);
    box-shadow: $shadow-md;
    transform: translateY(-2px);
  }
  
  i {
    font-size: $font-lg;
  }
  
  @media (max-width: 768px) {
    justify-content: center;
    padding: $spacing-md;
  }
}

.app-main {
  min-height: 600px;
  background: $bg-card;
  border-radius: 20px;
  padding: $spacing-xl;
  box-shadow: $shadow-xl;
  border: 1px solid $bg-accent;
}

.tab-content {
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

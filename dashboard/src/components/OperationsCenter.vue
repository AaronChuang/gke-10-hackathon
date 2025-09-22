<template>
  <div class="operations-center">
    <div class="header">
      <h2 class="title">
        <i class="fas fa-chart-line"></i>
        {{ $t('operations.title') }}
      </h2>
      <p class="subtitle">
        {{ $t('operations.subtitle') }}
      </p>
    </div>

    <div class="tabs">
      <button 
        :class="['tab-button', { active: activeTab === 'tasks' }]"
        @click="activeTab = 'tasks'"
      >
        <i class="fas fa-tasks"></i>
        {{ $t('operations.tabs.tasks') }}
      </button>
      <button 
        :class="['tab-button', { active: activeTab === 'conversations' }]"
        @click="activeTab = 'conversations'"
      >
        <i class="fas fa-comments"></i>
        {{ $t('operations.tabs.conversations') }}
      </button>
    </div>

    <!-- Task Management -->
    <div v-if="activeTab === 'tasks'" class="tab-content">
      <div class="stats-cards">
        <div class="stat-card">
          <i class="fas fa-clipboard-list"></i>
          <div class="stat-info">
            <h3>{{ taskStats.total }}</h3>
            <p>{{ $t('operations.stats.total') }}</p>
          </div>
        </div>
        <div class="stat-card">
          <i class="fas fa-clock"></i>
          <div class="stat-info">
            <h3>{{ taskStats.pending }}</h3>
            <p>{{ $t('operations.stats.pending') }}</p>
          </div>
        </div>
        <div class="stat-card">
          <i class="fas fa-check-circle"></i>
          <div class="stat-info">
            <h3>{{ taskStats.completed }}</h3>
            <p>{{ $t('operations.stats.completed') }}</p>
          </div>
        </div>
        <div class="stat-card">
          <i class="fas fa-coins"></i>
          <div class="stat-info">
            <h3>{{ formatTokens(taskStats.totalTokens) }}</h3>
            <p>{{ $t('operations.stats.tokens') }}</p>
          </div>
        </div>
      </div>

      <div class="task-table">
        <div class="table-header">
          <div class="header-cell">{{ $t('operations.tasks.table.taskId') }}</div>
          <div class="header-cell">{{ $t('operations.tasks.table.status') }}</div>
          <div class="header-cell">{{ $t('operations.tasks.table.creator') }}</div>
          <div class="header-cell">{{ $t('operations.tasks.table.currentDept') }}</div>
          <div class="header-cell">{{ $t('operations.tasks.table.tokens') }}</div>
          <div class="header-cell">{{ $t('operations.tasks.table.created') }}</div>
          <div class="header-cell">{{ $t('operations.tasks.table.actions') }}</div>
        </div>
        
        <div v-for="task in tasks" :key="task.task_id" class="table-row">
          <div class="cell task-id">{{ task.task_id.slice(0, 8) }}...</div>
          <div class="cell">
            <span :class="['status', task.status.toLowerCase()]">
              {{ getStatusText(task.status) }}
            </span>
          </div>
          <div class="cell">{{ task.user_id || $t('common.system') }}</div>
          <div class="cell">{{ getCurrentAgent(task) }}</div>
          <div class="cell token-count">{{ formatTokens(task.total_tokens?.total_tokens || 0) }}</div>
          <div class="cell">{{ formatDate(task.created_at) }}</div>
          <div class="cell">
            <button @click="viewTaskDetails(task)" class="action-button" :title="$t('operations.tasks.table.view')">
              <i class="fas fa-eye"></i>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Conversation History -->
    <div v-if="activeTab === 'conversations'" class="tab-content">
      <!-- Debug info -->
      <div v-if="conversationsLoading" class="loading-state">
        <i class="fas fa-spinner fa-spin"></i>
        {{ $t('operations.conversations.loading') }}
      </div>
      <div v-else-if="conversationsError" class="error-state">
        <i class="fas fa-exclamation-triangle"></i>
        {{ conversationsError }}
      </div>
      <div v-else-if="conversations.length === 0" class="empty-state">
        <i class="fas fa-comments"></i>
        <p>{{ $t('operations.conversations.noConversations') }}</p>
      </div>
      
      <div v-else class="conversation-list">
        <div v-for="conversation in conversations" :key="conversation.session_id" class="conversation-card">
          <div class="conversation-header">
            <div class="user-info">
              <i class="fas fa-user"></i>
              <span>{{ conversation.context?.user_id || $t('operations.conversations.anonymous') }}</span>
            </div>
            <div class="conversation-meta">
              <span class="message-count">{{ conversation.summary.total_messages }} {{ $t('operations.conversations.messageCount') }}</span>
              <span class="status-badge" :class="getConversationStatusClass(conversation.status)">{{ getConversationStatusText(conversation.status) }}</span>
            </div>
          </div>
          
          <div class="conversation-preview">
            <div v-if="conversation.messages?.length" class="last-message">
              <strong>{{ $t('operations.conversations.lastMessage') }}</strong>
              {{ conversation.messages[conversation.messages.length - 1]?.content?.slice(0, 100) }}...
            </div>
          </div>
          
          <div class="conversation-footer">
            <span class="timestamp">{{ formatDate(conversation.updated_at) }}</span>
            <button @click="viewConversation(conversation)" class="view-button">
              {{ $t('operations.conversations.viewDetails') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Task Details Modal -->
    <div v-if="selectedTask" class="modal-overlay" @click="closeTaskModal">
      <div class="modal task-modal" @click.stop>
        <div class="modal-header">
          <h3>{{ $t('operations.tasks.modal.title') }} - {{ selectedTask.task_id.slice(0, 8) }}...</h3>
          <button @click="closeTaskModal" class="close-button">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="modal-content">
          <div class="task-info">
            <div class="info-row">
              <span class="label">{{ $t('operations.tasks.modal.status') }}</span>
              <span :class="['status', selectedTask.status.toLowerCase()]">
                {{ getStatusText(selectedTask.status) }}
              </span>
            </div>
            <div class="info-row">
              <span class="label">{{ $t('operations.tasks.modal.created') }}</span>
              <span>{{ formatDateTime(selectedTask.created_at) }}</span>
            </div>
            <div class="info-row">
              <span class="label">{{ $t('operations.tasks.modal.tokens') }}</span>
              <span>{{ formatTokens(selectedTask.total_tokens?.total_tokens || 0) }}</span>
            </div>
          </div>

          <div class="execution-log">
            <h4>{{ $t('operations.tasks.modal.executionLog') }}</h4>
            <div class="log-entries">
              <div v-for="(entry, index) in selectedTask.log" :key="index" class="log-entry">
                <div class="log-header">
                  <span class="timestamp">{{ formatDateTime(entry.timestamp) }}</span>
                  <span class="agent">{{ entry.agent_id }}</span>
                </div>
                <div class="log-event">{{ entry.event }}</div>
                <div v-if="entry.details" class="log-details">
                  <pre>{{ JSON.stringify(entry.details, null, 2) }}</pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Conversation Details Modal -->
    <div v-if="selectedConversation" class="modal-overlay" @click="closeConversationModal">
      <div class="modal conversation-modal" @click.stop>
        <div class="modal-header">
          <h3>{{ $t('operations.conversations.details') }} - {{ selectedConversation.session_id.slice(0, 8) }}...</h3>
          <button @click="closeConversationModal" class="close-button">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="modal-content">
          <div class="conversation-info">
            <div class="info-row">
              <span class="label">{{ $t('operations.conversations.user') }}:</span>
              <span>{{ selectedConversation.context?.user_id || $t('operations.conversations.anonymous') }}</span>
            </div>
            <div class="info-row">
              <span class="label">{{ $t('operations.conversations.messageCount') }}:</span>
              <span>{{ selectedConversation.summary.total_messages }}</span>
            </div>
            <div class="info-row">
              <span class="label">{{ $t('operations.conversations.statusLabel') }}:</span>
              <span :class="['status-badge', getConversationStatusClass(selectedConversation.status)]">
                {{ getConversationStatusText(selectedConversation.status) }}
              </span>
            </div>
            <div class="info-row">
              <span class="label">{{ $t('operations.conversations.lastUpdate') }}:</span>
              <span>{{ formatDateTime(selectedConversation.updated_at) }}</span>
            </div>
          </div>

          <div class="conversation-messages">
            <h4>{{ $t('operations.conversations.messages') }}</h4>
            <div class="messages-list">
              <div v-for="(message, index) in selectedConversation.messages" :key="index" class="message-item">
                <div class="message-header">
                  <span class="sender">{{ message.sender === 'user' ? $t('operations.conversations.user') : $t('operations.conversations.agent') }}</span>
                  <span class="timestamp">{{ formatDateTime(message.timestamp / 1000) }}</span>
                </div>
                <div class="message-content">{{ message.content }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useConversations, type Conversation } from '@/composables/useConversations'

interface Task {
  task_id: string
  status: string
  user_id?: string
  created_at: number
  updated_at: number
  total_tokens?: {
    total_tokens: number
  }
  log: Array<{
    timestamp: number
    event: string
    agent_id: string
    details?: any
  }>
  agent_history: Array<{
    agent_id: string
    timestamp: number
    action: string
  }>
}

// Conversation interface is now imported from useConversations composable

const { t } = useI18n()
const props = defineProps<{
  tasks: Task[]
}>()

const activeTab = ref('tasks')
const selectedTask = ref<Task | null>(null)
const selectedConversation = ref<Conversation | null>(null)

// Use conversations composable
const { 
  conversations, 
  loading: conversationsLoading,
  error: conversationsError,
  loadConversations 
} = useConversations()

const taskStats = computed(() => {
  const tasks = props.tasks || []
  return {
    total: tasks.length,
    pending: tasks.filter(t => t.status === 'PENDING').length,
    completed: tasks.filter(t => t.status === 'COMPLETED').length,
    totalTokens: tasks.reduce((sum, t) => sum + (t.total_tokens?.total_tokens || 0), 0)
  }
})

const getStatusText = (status: string) => {
  const statusKey = status.toLowerCase()
  return t(`operations.tasks.status.${statusKey}`) || status
}

const getCurrentAgent = (task: Task) => {
  if (!task.agent_history?.length) return t('common.unassigned')
  const latest = task.agent_history[task.agent_history.length - 1]
  return latest.agent_id || t('common.unknown')
}

const getConversationStatusClass = (status: string) => {
  switch (status.toLowerCase()) {
    case 'active': return 'status-active'
    case 'paused': return 'status-paused'
    case 'completed': return 'status-completed'
    case 'archived': return 'status-archived'
    default: return 'status-unknown'
  }
}

const getConversationStatusText = (status: string) => {
  const statusKey = status.toLowerCase()
  return t(`operations.conversations.status.${statusKey}`) || status
}

const formatTokens = (tokens: number) => {
  if (tokens >= 1000000) return `${(tokens / 1000000).toFixed(1)}M`
  if (tokens >= 1000) return `${(tokens / 1000).toFixed(1)}K`
  return tokens.toString()
}

const formatDate = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleDateString('zh-TW')
}

const formatDateTime = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleString('zh-TW')
}

const viewTaskDetails = (task: Task) => {
  selectedTask.value = task
}

const closeTaskModal = () => {
  selectedTask.value = null
}

const viewConversation = (conversation: Conversation) => {
  selectedConversation.value = conversation
}

const closeConversationModal = () => {
  selectedConversation.value = null
}

// Conversations are now loaded via useConversations composable

onMounted(() => {
  loadConversations()
})
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as *;

.operations-center {
  height: 100%;
}

.header {
  margin-bottom: $spacing-xl;

  .title {
    font-size: $font-2xl;
    font-weight: 700;
    color: $text-primary;
    display: flex;
    align-items: center;
    gap: $spacing-md;
    margin-bottom: $spacing-sm;

    i {
      color: #8b5cf6;
    }
  }

  .subtitle {
    color: $text-secondary;
    font-size: $font-base;
  }
}

.tabs {
  display: flex;
  gap: $spacing-sm;
  margin-bottom: $spacing-xl;
  background: $bg-accent;
  border-radius: 12px;
  padding: $spacing-xs;
}

.tab-button {
  flex: 1;
  background: transparent;
  border: none;
  padding: $spacing-md;
  border-radius: 8px;
  cursor: pointer;
  transition: all $transition-normal;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-sm;
  color: $text-secondary;

  &.active {
    background: white;
    color: $text-primary;
    box-shadow: $shadow-sm;
  }
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: $spacing-lg;
  margin-bottom: $spacing-xl;
}

.stat-card {
  background: $bg-card;
  border: 1px solid $bg-accent;
  border-radius: 12px;
  padding: $spacing-lg;
  display: flex;
  align-items: center;
  gap: $spacing-md;

  i {
    font-size: $font-2xl;
    color: #8b5cf6;
  }

  .stat-info {
    h3 {
      font-size: $font-xl;
      font-weight: 700;
      color: $text-primary;
      margin-bottom: $spacing-xs;
    }

    p {
      color: $text-secondary;
      font-size: $font-sm;
    }
  }
}

.task-table {
  background: $bg-card;
  border: 1px solid $bg-accent;
  border-radius: 12px;
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 1fr 100px 120px 150px 100px 120px 60px;
  background: $bg-accent;
  padding: $spacing-md;
  font-weight: 600;
  color: $text-primary;
}

.table-row {
  display: grid;
  grid-template-columns: 1fr 100px 120px 150px 100px 120px 60px;
  padding: $spacing-md;
  border-bottom: 1px solid $bg-accent;
  align-items: center;

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: $bg-hover;
  }
}

.cell {
  font-size: $font-sm;
  color: $text-primary;

  &.task-id {
    font-family: monospace;
    color: #3b82f6;
  }

  &.token-count {
    font-weight: 600;
    color: #10b981;
  }
}

.status {
  padding: $spacing-xs $spacing-sm;
  border-radius: 6px;
  font-size: $font-xs;
  font-weight: 500;

  &.pending {
    background: #fef3c7;
    color: #92400e;
  }

  &.running {
    background: #dbeafe;
    color: #1e40af;
  }

  &.completed {
    background: #d1fae5;
    color: #065f46;
  }

  &.failed {
    background: #fee2e2;
    color: #991b1b;
  }
}

.status-badge {
  padding: $spacing-xs $spacing-sm;
  border-radius: 6px;
  font-size: $font-xs;
  font-weight: 500;

  &.status-active {
    background: #dbeafe;
    color: #1e40af;
  }

  &.status-paused {
    background: #fef3c7;
    color: #92400e;
  }

  &.status-completed {
    background: #d1fae5;
    color: #065f46;
  }

  &.status-archived {
    background: #f3f4f6;
    color: #6b7280;
  }

  &.status-unknown {
    background: #fee2e2;
    color: #991b1b;
  }
}

.action-button {
  background: $bg-accent;
  border: none;
  border-radius: 6px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: $text-secondary;
  transition: all $transition-normal;

  &:hover {
    background: #3b82f6;
    color: white;
  }
}

.conversation-list {
  display: grid;
  gap: $spacing-lg;
}

.conversation-card {
  background: $bg-card;
  border: 1px solid $bg-accent;
  border-radius: 12px;
  padding: $spacing-lg;
}

.conversation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $spacing-md;

  .user-info {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    font-weight: 600;
    color: $text-primary;
  }

  .conversation-meta {
    display: flex;
    gap: $spacing-md;
    font-size: $font-sm;
    color: $text-secondary;
  }
}

.conversation-preview {
  margin-bottom: $spacing-md;
  color: $text-secondary;
  font-size: $font-sm;
}

.conversation-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .timestamp {
    color: $text-secondary;
    font-size: $font-sm;
  }

  .view-button {
    background: linear-gradient(135deg, #3b82f6, #1d4ed8);
    color: white;
    border: none;
    border-radius: 8px;
    padding: $spacing-sm $spacing-md;
    cursor: pointer;
    font-size: $font-sm;
    transition: all $transition-normal;

    &:hover {
      transform: translateY(-1px);
      box-shadow: $shadow-sm;
    }
  }
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: $spacing-lg;
}

.modal {
  background: $bg-card;
  border-radius: 16px;
  width: 100%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: $shadow-xl;

  &.task-modal {
    max-width: 900px;
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-xl;
  border-bottom: 1px solid $bg-accent;

  h3 {
    font-size: $font-xl;
    font-weight: 600;
    color: $text-primary;
  }

  .close-button {
    background: none;
    border: none;
    font-size: $font-lg;
    color: $text-secondary;
    cursor: pointer;
    padding: $spacing-sm;
    border-radius: 8px;
    transition: all $transition-normal;

    &:hover {
      background: $bg-accent;
      color: $text-primary;
    }
  }
}

.modal-content {
  padding: $spacing-xl;
}

.task-info {
  margin-bottom: $spacing-xl;

  .info-row {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    margin-bottom: $spacing-md;

    .label {
      font-weight: 600;
      color: $text-secondary;
      min-width: 100px;
    }
  }
}

.execution-log {
  h4 {
    font-size: $font-lg;
    font-weight: 600;
    color: $text-primary;
    margin-bottom: $spacing-lg;
  }
}

.log-entries {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.log-entry {
  background: $bg-accent;
  border-radius: 8px;
  padding: $spacing-md;

  .log-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: $spacing-sm;
    font-size: $font-sm;

    .timestamp {
      color: $text-secondary;
    }

    .agent {
      color: #3b82f6;
      font-weight: 600;
    }
  }

  .log-event {
    font-weight: 600;
    color: $text-primary;
    margin-bottom: $spacing-sm;
  }

  .log-details {
    background: $bg-primary;
    border-radius: 6px;
    padding: $spacing-sm;

    pre {
      font-size: $font-xs;
      color: $text-secondary;
      margin: 0;
      white-space: pre-wrap;
    }
  }
}

// 狀態顯示樣式
.loading-state, .error-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: $spacing-xl;
  color: $text-muted;
  
  i {
    font-size: 2rem;
    margin-bottom: $spacing-md;
    
    &.fa-spinner {
      animation: spin 1s linear infinite;
    }
  }
  
  p {
    margin: 0;
    font-size: $font-base;
  }
}

.error-state {
  color: #dc2626;
  
  i {
    color: #ef4444;
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.conversation-modal {
  max-width: 800px;
  max-height: 80vh;
  
  .conversation-info {
    margin-bottom: $spacing-lg;
    
    .info-row {
      display: flex;
      justify-content: space-between;
      padding: $spacing-sm 0;
      border-bottom: 1px solid $bg-accent;
      
      .label {
        font-weight: 500;
        color: $text-secondary;
      }
    }
  }
  
  .conversation-messages {
    h4 {
      margin-bottom: $spacing-md;
      color: $text-primary;
    }
    
    .messages-list {
      max-height: 400px;
      overflow-y: auto;
      border: 1px solid $bg-accent;
      border-radius: 8px;
      
      .message-item {
        padding: $spacing-md;
        border-bottom: 1px solid $bg-accent;
        
        &:last-child {
          border-bottom: none;
        }
        
        .message-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: $spacing-sm;
          
          .sender {
            font-weight: 500;
            color: $text-primary;
          }
          
          .timestamp {
            color: $text-muted;
            font-size: $font-sm;
          }
        }
        
        .message-content {
          color: $text-secondary;
          line-height: 1.5;
        }
      }
    }
  }
}
</style>

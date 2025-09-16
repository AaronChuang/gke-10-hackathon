<template>
  <div class="task-dashboard">
    <div class="dashboard-header">
      <h2 class="section-title">任務監控儀表板</h2>
      <div class="stats-cards">
        <div class="stat-card">
          <div class="stat-value">{{ totalTasks }}</div>
          <div class="stat-label">總任務數</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ runningTasks }}</div>
          <div class="stat-label">執行中</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ completedTasks }}</div>
          <div class="stat-label">已完成</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ totalTokens.toLocaleString() }}</div>
          <div class="stat-label">總 Token 消耗</div>
        </div>
      </div>
    </div>

    <div class="task-table-container">
      <div class="table-header">
        <h3>任務列表</h3>
        <div class="table-controls">
          <select v-model="statusFilter" class="filter-select">
            <option value="">所有狀態</option>
            <option value="PENDING">待處理</option>
            <option value="RUNNING">執行中</option>
            <option value="COMPLETED">已完成</option>
            <option value="FAILED">失敗</option>
          </select>
        </div>
      </div>

      <div class="table-wrapper">
        <table class="task-table">
          <thead>
            <tr>
              <th>任務 ID</th>
              <th>狀態</th>
              <th>初始提示</th>
              <th>代理人執行</th>
              <th>Token 消耗</th>
              <th>創建時間</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="task in filteredTasks" :key="task.task_id" :class="getRowClass(task.status)">
              <td class="task-id">{{ task.task_id.slice(0, 8) }}...</td>
              <td>
                <span :class="['status-badge', getStatusClass(task.status)]">
                  {{ getStatusText(task.status) }}
                </span>
              </td>
              <td class="task-prompt">{{ truncateText(task.initial_prompt, 50) }}</td>
              <td class="agent-info">
                <div v-if="task.agent_history && task.agent_history.length > 0">
                  <div v-for="agent in task.agent_history" :key="agent.agent_name" class="agent-entry">
                    <span class="agent-name">{{ agent.agent_name }}</span>
                    <span :class="['agent-status', getAgentStatusClass(agent.status)]">
                      {{ agent.status }}
                    </span>
                  </div>
                </div>
                <span v-else class="no-agents">尚未分配</span>
              </td>
              <td class="token-info">
                <div v-if="task.total_tokens">
                  <div class="token-row">
                    <span class="token-type">輸入:</span>
                    <span class="token-value">{{ task.total_tokens.input_tokens.toLocaleString() }}</span>
                  </div>
                  <div class="token-row">
                    <span class="token-type">輸出:</span>
                    <span class="token-value">{{ task.total_tokens.output_tokens.toLocaleString() }}</span>
                  </div>
                  <div v-if="task.total_tokens.total_cost_usd" class="token-row cost">
                    <span class="token-type">成本:</span>
                    <span class="token-value">${{ task.total_tokens.total_cost_usd.toFixed(4) }}</span>
                  </div>
                </div>
                <span v-else class="no-tokens">-</span>
              </td>
              <td class="created-time">{{ formatTime(task.created_at) }}</td>
              <td class="actions">
                <button @click="viewTaskDetails(task)" class="action-btn view-btn">
                  <i class="fas fa-eye"></i>
                </button>
                <button @click="viewTaskLogs(task)" class="action-btn log-btn">
                  <i class="fas fa-list"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 任務詳情模態框 -->
    <div v-if="selectedTask" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>任務詳情</h3>
          <button @click="closeModal" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <div class="detail-section">
            <h4>基本信息</h4>
            <div class="detail-grid">
              <div class="detail-item">
                <label>任務 ID:</label>
                <span>{{ selectedTask.task_id }}</span>
              </div>
              <div class="detail-item">
                <label>狀態:</label>
                <span :class="['status-badge', getStatusClass(selectedTask.status)]">
                  {{ getStatusText(selectedTask.status) }}
                </span>
              </div>
              <div class="detail-item">
                <label>創建時間:</label>
                <span>{{ formatTime(selectedTask.created_at) }}</span>
              </div>
            </div>
          </div>

          <div class="detail-section">
            <h4>初始提示</h4>
            <div class="prompt-content">{{ selectedTask.initial_prompt }}</div>
          </div>

          <div v-if="selectedTask.agent_history && selectedTask.agent_history.length > 0" class="detail-section">
            <h4>代理人執行歷史</h4>
            <div class="agent-history">
              <div v-for="agent in selectedTask.agent_history" :key="agent.agent_name" class="agent-detail">
                <div class="agent-header">
                  <span class="agent-name">{{ agent.agent_name }}</span>
                  <span :class="['agent-status', getAgentStatusClass(agent.status)]">
                    {{ agent.status }}
                  </span>
                </div>
                <div class="agent-tokens">
                  <span>輸入 Token: {{ agent.input_tokens.toLocaleString() }}</span>
                  <span>輸出 Token: {{ agent.output_tokens.toLocaleString() }}</span>
                </div>
                <div class="agent-time">
                  開始: {{ formatTime(agent.started_at) }}
                  <span v-if="agent.completed_at">
                    | 完成: {{ formatTime(agent.completed_at) }}
                  </span>
                </div>
                <div v-if="agent.error_message" class="agent-error">
                  錯誤: {{ agent.error_message }}
                </div>
              </div>
            </div>
          </div>

          <div v-if="selectedTask.log && selectedTask.log.length > 0" class="detail-section">
            <h4>執行日誌</h4>
            <div class="log-entries">
              <div v-for="log in selectedTask.log" :key="log.timestamp" 
                   :class="['log-entry', `log-${log.level.toLowerCase()}`]">
                <div class="log-header">
                  <span class="log-time">{{ formatTime(log.timestamp) }}</span>
                  <span class="log-level">{{ log.level }}</span>
                  <span v-if="log.agent_name" class="log-agent">{{ log.agent_name }}</span>
                </div>
                <div class="log-message">{{ log.message }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Task } from '@/types/task'

interface Props {
  tasks: Task[]
}

const props = defineProps<Props>()

const statusFilter = ref('')
const selectedTask = ref<Task | null>(null)

const filteredTasks = computed(() => {
  if (!statusFilter.value) return props.tasks
  return props.tasks.filter(task => task.status === statusFilter.value)
})

const totalTasks = computed(() => props.tasks.length)
const runningTasks = computed(() => props.tasks.filter(t => t.status.includes('RUNNING')).length)
const completedTasks = computed(() => props.tasks.filter(t => t.status === 'COMPLETED').length)
const totalTokens = computed(() => {
  return props.tasks.reduce((sum, task) => {
    if (task.total_tokens) {
      return sum + task.total_tokens.input_tokens + task.total_tokens.output_tokens
    }
    return sum
  }, 0)
})

const getRowClass = (status: string) => {
  if (status.includes('RUNNING')) return 'running-row'
  if (status === 'COMPLETED') return 'completed-row'
  if (status === 'FAILED') return 'failed-row'
  return ''
}

const getStatusClass = (status: string) => {
  if (status.includes('RUNNING')) return 'status-running'
  if (status === 'COMPLETED') return 'status-completed'
  if (status === 'FAILED') return 'status-failed'
  return 'status-pending'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'PENDING': '待處理',
    'RUNNING': '執行中',
    'TECH_ANALYST_RUNNING': '技術分析中',
    'ARCHITECT_RUNNING': '架構設計中',
    'STYLIST_RUNNING': '樣式設計中',
    'COMPLETED': '已完成',
    'FAILED': '失敗'
  }
  return statusMap[status] || status
}

const getAgentStatusClass = (status: string) => {
  if (status === 'RUNNING') return 'agent-running'
  if (status === 'COMPLETED') return 'agent-completed'
  if (status === 'FAILED') return 'agent-failed'
  return ''
}

const truncateText = (text: string, maxLength: number) => {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

const formatTime = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleString('zh-TW')
}

const viewTaskDetails = (task: Task) => {
  selectedTask.value = task
}

const viewTaskLogs = (task: Task) => {
  selectedTask.value = task
  // 可以添加滾動到日誌部分的邏輯
}

const closeModal = () => {
  selectedTask.value = null
}
</script>

<style lang="scss" scoped>
.task-dashboard {
  padding: $spacing-lg;
}

.dashboard-header {
  margin-bottom: $spacing-xl;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: $spacing-lg;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: $spacing-md;
  margin-bottom: $spacing-lg;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: $spacing-lg;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  text-align: center;
  
  .stat-value {
    font-size: 2rem;
    font-weight: 700;
    color: #3b82f6;
    margin-bottom: $spacing-xs;
  }
  
  .stat-label {
    color: $text-muted;
    font-size: 0.875rem;
  }
}

.task-table-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $spacing-lg;
  border-bottom: 1px solid #e5e7eb;
  
  h3 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 600;
  }
}

.filter-select {
  padding: $spacing-sm $spacing-md;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
}

.table-wrapper {
  overflow-x: auto;
}

.task-table {
  width: 100%;
  border-collapse: collapse;
  
  th, td {
    padding: $spacing-md;
    text-align: left;
    border-bottom: 1px solid #f3f4f6;
  }
  
  th {
    background-color: #f9fafb;
    font-weight: 600;
    color: $text-primary;
    font-size: 0.875rem;
  }
  
  .running-row {
    background-color: #fef3c7;
  }
  
  .completed-row {
    background-color: #d1fae5;
  }
  
  .failed-row {
    background-color: #fee2e2;
  }
}

.task-id {
  font-family: monospace;
  font-size: 0.875rem;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  
  &.status-pending {
    background-color: #f3f4f6;
    color: #6b7280;
  }
  
  &.status-running {
    background-color: #fbbf24;
    color: #92400e;
  }
  
  &.status-completed {
    background-color: #10b981;
    color: white;
  }
  
  &.status-failed {
    background-color: #ef4444;
    color: white;
  }
}

.task-prompt {
  max-width: 200px;
  font-size: 0.875rem;
}

.agent-info {
  min-width: 150px;
  
  .agent-entry {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
    font-size: 0.75rem;
    
    .agent-name {
      font-weight: 500;
    }
    
    .agent-status {
      padding: 2px 6px;
      border-radius: 8px;
      
      &.agent-running {
        background-color: #fbbf24;
        color: #92400e;
      }
      
      &.agent-completed {
        background-color: #10b981;
        color: white;
      }
      
      &.agent-failed {
        background-color: #ef4444;
        color: white;
      }
    }
  }
  
  .no-agents {
    color: $text-muted;
    font-style: italic;
    font-size: 0.875rem;
  }
}

.token-info {
  min-width: 120px;
  
  .token-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.75rem;
    margin-bottom: 2px;
    
    .token-type {
      color: $text-muted;
    }
    
    .token-value {
      font-weight: 500;
    }
    
    &.cost {
      color: #059669;
      font-weight: 600;
    }
  }
  
  .no-tokens {
    color: $text-muted;
    font-style: italic;
  }
}

.created-time {
  font-size: 0.875rem;
  color: $text-muted;
}

.actions {
  .action-btn {
    padding: 6px 8px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    margin-right: 4px;
    font-size: 0.75rem;
    
    &.view-btn {
      background-color: #3b82f6;
      color: white;
    }
    
    &.log-btn {
      background-color: #6b7280;
      color: white;
    }
    
    &:hover {
      opacity: 0.8;
    }
  }
}

// 模態框樣式
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  max-width: 800px;
  max-height: 80vh;
  overflow-y: auto;
  width: 90%;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $spacing-lg;
  border-bottom: 1px solid #e5e7eb;
  
  h3 {
    margin: 0;
  }
  
  .close-btn {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: $text-muted;
  }
}

.modal-body {
  padding: $spacing-lg;
}

.detail-section {
  margin-bottom: $spacing-xl;
  
  h4 {
    margin-bottom: $spacing-md;
    color: $text-primary;
    font-size: 1.1rem;
  }
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: $spacing-md;
}

.detail-item {
  display: flex;
  flex-direction: column;
  
  label {
    font-weight: 600;
    color: $text-muted;
    font-size: 0.875rem;
    margin-bottom: 4px;
  }
  
  span {
    font-size: 0.875rem;
  }
}

.prompt-content {
  background-color: #f9fafb;
  padding: $spacing-md;
  border-radius: 6px;
  font-size: 0.875rem;
  line-height: 1.5;
}

.agent-history {
  .agent-detail {
    background-color: #f9fafb;
    padding: $spacing-md;
    border-radius: 6px;
    margin-bottom: $spacing-md;
    
    .agent-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: $spacing-sm;
      
      .agent-name {
        font-weight: 600;
      }
    }
    
    .agent-tokens, .agent-time {
      font-size: 0.875rem;
      color: $text-muted;
      margin-bottom: 4px;
      
      span {
        margin-right: $spacing-md;
      }
    }
    
    .agent-error {
      color: #ef4444;
      font-size: 0.875rem;
      margin-top: $spacing-sm;
    }
  }
}

.log-entries {
  max-height: 300px;
  overflow-y: auto;
  
  .log-entry {
    padding: $spacing-sm;
    border-left: 3px solid #e5e7eb;
    margin-bottom: $spacing-sm;
    
    &.log-info {
      border-left-color: #3b82f6;
    }
    
    &.log-warning {
      border-left-color: #f59e0b;
    }
    
    &.log-error {
      border-left-color: #ef4444;
    }
    
    .log-header {
      display: flex;
      gap: $spacing-sm;
      margin-bottom: 4px;
      font-size: 0.75rem;
      
      .log-time {
        color: $text-muted;
      }
      
      .log-level {
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
        background-color: #f3f4f6;
      }
      
      .log-agent {
        color: #6b7280;
      }
    }
    
    .log-message {
      font-size: 0.875rem;
    }
  }
}
</style>

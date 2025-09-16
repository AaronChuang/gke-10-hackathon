<template>
  <div class="task-table-wrapper">
    <div v-if="tasks.length === 0" class="no-tasks">
      <p>目前沒有任何任務。</p>
    </div>
    
    <div v-else class="table-container">
      <table class="task-table">
        <thead>
          <tr>
            <th>任務 ID</th>
            <th>狀態</th>
            <th>初始提示</th>
            <th>建立時間</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="task in tasks" 
            :key="task.task_id"
            class="task-row hover-bg-gray-800 transition-colors"
          >
            <td class="task-id">
              {{ task.task_id.substring(0, 8) }}...
            </td>
            <td class="task-status">
              <span 
                class="status-badge"
                :class="[
                  `status-${task.status || 'PENDING'}`,
                  { 'blinking': isRunningStatus(task.status) }
                ]"
              >
                {{ task.status || 'PENDING' }}
              </span>
            </td>
            <td class="task-prompt" :title="task.initial_prompt">
              {{ task.initial_prompt }}
            </td>
            <td class="task-created">
              {{ formatDate(task.created_at) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Task, TaskStatus } from '@/types/task'

interface Props {
  tasks: Task[]
}

defineProps<Props>()

const isRunningStatus = (status: TaskStatus): boolean => {
  return status?.includes('RUNNING') || false
}

const formatDate = (timestamp: number): string => {
  if (!timestamp) return 'N/A'
  
  return new Date(timestamp * 1000).toLocaleString('zh-TW', { 
    timeZone: 'Asia/Taipei',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}
</script>

<style lang="scss" scoped>
.task-table-wrapper {
  background-color: $bg-secondary;
  border-radius: $radius-lg;
  box-shadow: $shadow-xl;
  overflow: hidden;
}

.no-tasks {
  text-align: center;
  padding: $spacing-2xl;
  color: $text-gray;
}

.table-container {
  overflow-x: auto;
}

.task-table {
  width: 100%;
  border-collapse: collapse;
  
  thead {
    background-color: $bg-card;
    
    th {
      padding: $spacing-sm $spacing-lg;
      text-align: left;
      font-size: 0.75rem;
      font-weight: 500;
      color: $text-muted;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      border-bottom: 1px solid $bg-hover;
    }
  }
  
  tbody {
    background-color: $bg-secondary;
    
    .task-row {
      border-bottom: 1px solid $bg-hover;
      
      &:last-child {
        border-bottom: none;
      }
      
      td {
        padding: $spacing-md $spacing-lg;
        vertical-align: top;
      }
    }
  }
}

.task-id {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.875rem;
  color: $text-muted;
  white-space: nowrap;
}

.task-status {
  white-space: nowrap;
}

.task-prompt {
  color: $text-secondary;
  font-size: 0.875rem;
  max-width: 20rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  
  @media (max-width: 768px) {
    max-width: 10rem;
  }
}

.task-created {
  color: $text-muted;
  font-size: 0.875rem;
  white-space: nowrap;
}
</style>

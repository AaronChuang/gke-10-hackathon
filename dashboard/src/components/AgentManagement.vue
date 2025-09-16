<template>
  <div class="agent-management">
    <div class="agent-header">
      <h2 class="section-title">代理人管理</h2>
      <button @click="showCreateModal = true" class="create-btn">
        <i class="fas fa-plus"></i>
        創建代理人
      </button>
    </div>

    <div class="stats-overview">
      <div class="stat-card">
        <div class="stat-value">{{ totalAgents }}</div>
        <div class="stat-label">總代理人數</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ activeAgents }}</div>
        <div class="stat-label">活躍代理人</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ creatingAgents }}</div>
        <div class="stat-label">創建中</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ failedAgents }}</div>
        <div class="stat-label">失敗</div>
      </div>
    </div>

    <div class="agent-table-container">
      <div class="table-header">
        <h3>代理人列表</h3>
        <div class="table-controls">
          <select v-model="statusFilter" class="filter-select">
            <option value="">所有狀態</option>
            <option value="ACTIVE">活躍</option>
            <option value="INACTIVE">非活躍</option>
            <option value="CREATING">創建中</option>
            <option value="FAILED">失敗</option>
          </select>
          <button @click="refreshAgents" class="refresh-btn">
            <i class="fas fa-sync-alt"></i>
            刷新
          </button>
        </div>
      </div>

      <div class="table-wrapper">
        <table class="agent-table">
          <thead>
            <tr>
              <th>代理人名稱</th>
              <th>描述</th>
              <th>狀態</th>
              <th>能力標籤</th>
              <th>Pub/Sub 主題</th>
              <th>創建時間</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="agent in filteredAgents" :key="agent.agent_id" :class="getRowClass(agent.status)">
              <td class="agent-name">
                <div class="name-content">
                  <i class="fas fa-robot agent-icon"></i>
                  <span class="name-text">{{ agent.name }}</span>
                  <span v-if="agent.name === 'OrchestratorAgent'" class="system-badge">系統</span>
                </div>
              </td>
              <td class="agent-description">
                {{ truncateText(agent.description, 60) }}
              </td>
              <td>
                <span :class="['status-badge', getStatusClass(agent.status)]">
                  {{ getStatusText(agent.status) }}
                </span>
              </td>
              <td class="capabilities-cell">
                <div class="capabilities-container">
                  <span 
                    v-for="capability in agent.capabilities.slice(0, 3)" 
                    :key="capability"
                    class="capability-tag"
                  >
                    {{ capability }}
                  </span>
                  <span v-if="agent.capabilities.length > 3" class="more-capabilities">
                    +{{ agent.capabilities.length - 3 }}
                  </span>
                </div>
              </td>
              <td class="pubsub-topic">
                <code class="topic-code">{{ agent.pubsub_topic || '-' }}</code>
              </td>
              <td class="created-time">{{ formatTime(agent.created_at) }}</td>
              <td class="actions-cell">
                <button 
                  @click="viewAgentDetails(agent)" 
                  class="action-btn view-btn"
                  title="查看詳情"
                >
                  <i class="fas fa-eye"></i>
                </button>
                <button 
                  @click="editAgent(agent)" 
                  :disabled="agent.status === 'CREATING'"
                  class="action-btn edit-btn"
                  title="編輯"
                >
                  <i class="fas fa-edit"></i>
                </button>
                <button 
                  @click="toggleAgentStatus(agent)" 
                  :disabled="agent.status === 'CREATING' || agent.name === 'OrchestratorAgent'"
                  :class="['action-btn', agent.status === 'ACTIVE' ? 'deactivate-btn' : 'activate-btn']"
                  :title="agent.status === 'ACTIVE' ? '停用' : '啟用'"
                >
                  <i :class="agent.status === 'ACTIVE' ? 'fas fa-pause' : 'fas fa-play'"></i>
                </button>
                <button 
                  @click="deleteAgent(agent)" 
                  :disabled="agent.status === 'CREATING' || agent.name === 'OrchestratorAgent'"
                  class="action-btn delete-btn"
                  title="刪除"
                >
                  <i class="fas fa-trash"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <!-- 創建代理人模態框 -->
    <div v-if="showCreateModal" class="modal-overlay" @click="closeCreateModal">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h3>創建新代理人</h3>
          <button @click="closeCreateModal" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="submitCreateAgent">
            <div class="form-row">
              <div class="form-group">
                <label for="agent-name">代理人名稱 *</label>
                <input 
                  id="agent-name"
                  v-model="createForm.name" 
                  type="text" 
                  placeholder="例如：MarketingAgent"
                  required
                  class="form-input"
                />
              </div>
              <div class="form-group">
                <label for="pubsub-topic">Pub/Sub 主題</label>
                <input 
                  id="pubsub-topic"
                  v-model="createForm.pubsub_topic" 
                  type="text" 
                  placeholder="例如：marketing-agent-topic"
                  class="form-input"
                />
                <small class="form-help">留空將自動生成</small>
              </div>
            </div>

            <div class="form-group">
              <label for="agent-description">描述 *</label>
              <textarea 
                id="agent-description"
                v-model="createForm.description" 
                placeholder="描述代理人的主要功能和用途..."
                required
                class="form-textarea"
                rows="3"
              ></textarea>
            </div>

            <div class="form-group">
              <label for="capabilities">能力標籤</label>
              <div class="capabilities-input">
                <div class="selected-capabilities">
                  <span 
                    v-for="(capability, index) in createForm.capabilities" 
                    :key="index"
                    class="capability-tag removable"
                  >
                    {{ capability }}
                    <button type="button" @click="removeCapability(index)" class="remove-capability">
                      <i class="fas fa-times"></i>
                    </button>
                  </span>
                </div>
                <div class="add-capability">
                  <input 
                    v-model="newCapability"
                    @keydown.enter.prevent="addCapability"
                    type="text" 
                    placeholder="輸入能力標籤後按 Enter"
                    class="capability-input"
                  />
                  <button type="button" @click="addCapability" class="add-capability-btn">
                    <i class="fas fa-plus"></i>
                  </button>
                </div>
              </div>
              <small class="form-help">例如：文案撰寫、市場分析、數據處理等</small>
            </div>

            <div class="form-group">
              <label for="system-prompt">系統提示詞 *</label>
              <textarea 
                id="system-prompt"
                v-model="createForm.system_prompt" 
                placeholder="定義代理人的角色、行為和回應風格..."
                required
                class="form-textarea"
                rows="8"
              ></textarea>
              <small class="form-help">這將決定代理人的個性和專業領域</small>
            </div>

            <div class="form-actions">
              <button type="button" @click="closeCreateModal" class="cancel-btn">取消</button>
              <button type="submit" :disabled="submitting" class="submit-btn">
                <i v-if="submitting" class="fas fa-spinner fa-spin"></i>
                {{ submitting ? '創建中...' : '創建代理人' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Agent } from '@/types/agent'

interface Props {
  agents: Agent[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  refresh: []
}>()

const statusFilter = ref('')
const showCreateModal = ref(false)
const submitting = ref(false)
const newCapability = ref('')

// 創建表單數據
const createForm = ref({
  name: '',
  description: '',
  system_prompt: '',
  capabilities: [] as string[],
  pubsub_topic: ''
})

const filteredAgents = computed(() => {
  if (!statusFilter.value) return props.agents
  return props.agents.filter(agent => agent.status === statusFilter.value)
})

const totalAgents = computed(() => props.agents.length)
const activeAgents = computed(() => props.agents.filter(a => a.status === 'ACTIVE').length)
const creatingAgents = computed(() => props.agents.filter(a => a.status === 'CREATING').length)
const failedAgents = computed(() => props.agents.filter(a => a.status === 'FAILED').length)

const getRowClass = (status: string) => {
  if (status === 'CREATING') return 'creating-row'
  if (status === 'ACTIVE') return 'active-row'
  if (status === 'FAILED') return 'failed-row'
  return 'inactive-row'
}

const getStatusClass = (status: string) => {
  switch (status) {
    case 'ACTIVE': return 'status-active'
    case 'INACTIVE': return 'status-inactive'
    case 'CREATING': return 'status-creating'
    case 'FAILED': return 'status-failed'
    default: return 'status-unknown'
  }
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'ACTIVE': '活躍',
    'INACTIVE': '非活躍',
    'CREATING': '創建中',
    'FAILED': '失敗'
  }
  return statusMap[status] || status
}

const truncateText = (text: string, maxLength: number) => {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

const formatTime = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleString('zh-TW')
}

const refreshAgents = () => {
  emit('refresh')
}

// 代理人操作函數
const viewAgentDetails = (agent: Agent) => {
  // 顯示代理人詳情模態框
  alert(`代理人詳情：\n名稱：${agent.name}\n描述：${agent.description}\n狀態：${agent.status}\n能力：${agent.capabilities.join(', ')}\n創建時間：${formatTime(agent.created_at)}`)
}

const editAgent = (agent: Agent) => {
  // 填充編輯表單
  createForm.value = {
    name: agent.name,
    description: agent.description,
    system_prompt: agent.system_prompt,
    capabilities: [...agent.capabilities],
    pubsub_topic: agent.pubsub_topic
  }
  showCreateModal.value = true
}

const toggleAgentStatus = async (agent: Agent) => {
  const newStatus = agent.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE'
  const action = newStatus === 'ACTIVE' ? '啟用' : '停用'
  
  if (confirm(`確定要${action}代理人 ${agent.name} 嗎？`)) {
    try {
      const response = await fetch(`/api/agents/${agent.agent_id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus })
      })

      if (response.ok) {
        emit('refresh')
      } else {
        const error = await response.json()
        alert(`${action}失敗: ${error.detail || '未知錯誤'}`)
      }
    } catch (error) {
      alert(`${action}失敗: ${error}`)
    }
  }
}

const deleteAgent = async (agent: Agent) => {
  if (agent.name === 'OrchestratorAgent') {
    alert('無法刪除系統核心代理人')
    return
  }

  if (confirm(`確定要刪除代理人 ${agent.name} 嗎？此操作無法復原。`)) {
    try {
      const response = await fetch(`/api/agents/${agent.agent_id}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        emit('refresh')
      } else {
        const error = await response.json()
        alert(`刪除失敗: ${error.detail || '未知錯誤'}`)
      }
    } catch (error) {
      alert(`刪除失敗: ${error}`)
    }
  }
}

// 創建代理人相關函數
const addCapability = () => {
  if (newCapability.value.trim() && !createForm.value.capabilities.includes(newCapability.value.trim())) {
    createForm.value.capabilities.push(newCapability.value.trim())
    newCapability.value = ''
  }
}

const removeCapability = (index: number) => {
  createForm.value.capabilities.splice(index, 1)
}

const resetCreateForm = () => {
  createForm.value = {
    name: '',
    description: '',
    system_prompt: '',
    capabilities: [],
    pubsub_topic: ''
  }
  newCapability.value = ''
}

const closeCreateModal = () => {
  showCreateModal.value = false
  resetCreateForm()
  submitting.value = false
}

const submitCreateAgent = async () => {
  if (!createForm.value.name || !createForm.value.description || !createForm.value.system_prompt) {
    alert('請填寫所有必填欄位')
    return
  }

  submitting.value = true
  try {
    const response = await fetch('/api/agents', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(createForm.value)
    })

    if (response.ok) {
      closeCreateModal()
      emit('refresh')
    } else {
      const error = await response.json()
      alert(`創建代理人失敗: ${error.detail || '未知錯誤'}`)
    }
  } catch (error) {
    alert(`創建代理人失敗: ${error}`)
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
.agent-management {
  padding: $spacing-lg;
}

.agent-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $spacing-xl;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: $text-primary;
  margin: 0;
}

.create-btn {
  background-color: #3b82f6;
  color: white;
  border: none;
  padding: $spacing-md $spacing-lg;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  
  &:hover {
    background-color: #2563eb;
  }
}

.stats-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: $spacing-md;
  margin-bottom: $spacing-xl;
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

.agent-table-container {
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
  
  .table-controls {
    display: flex;
    gap: $spacing-sm;
    align-items: center;
  }
}

.filter-select {
  padding: $spacing-sm $spacing-md;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
}

.refresh-btn {
  background-color: #6b7280;
  color: white;
  border: none;
  padding: $spacing-sm $spacing-md;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: $spacing-xs;
  
  &:hover {
    background-color: #4b5563;
  }
}

.table-wrapper {
  overflow-x: auto;
}

.agent-table {
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
  
  .creating-row {
    background-color: #dbeafe;
  }
  
  .active-row {
    background-color: #d1fae5;
  }
  
  .failed-row {
    background-color: #fee2e2;
  }
  
  .inactive-row {
    background-color: #f9fafb;
  }
}

.agent-name {
  .name-content {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
  }
  
  .agent-icon {
    color: #3b82f6;
    font-size: 1.1rem;
  }
  
  .name-text {
    font-weight: 600;
    color: $text-primary;
  }
  
  .system-badge {
    background-color: #fbbf24;
    color: #92400e;
    padding: 2px 6px;
    border-radius: 8px;
    font-size: 0.75rem;
    font-weight: 500;
  }
}

.agent-description {
  max-width: 250px;
  font-size: 0.875rem;
  color: $text-muted;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  
  &.status-active {
    background-color: #10b981;
    color: white;
  }
  
  &.status-inactive {
    background-color: #6b7280;
    color: white;
  }
  
  &.status-creating {
    background-color: #3b82f6;
    color: white;
  }
  
  &.status-failed {
    background-color: #ef4444;
    color: white;
  }
}

.capabilities-cell {
  max-width: 200px;
  
  .capabilities-container {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    align-items: center;
  }
  
  .capability-tag {
    background-color: #e5e7eb;
    color: #374151;
    padding: 2px 6px;
    border-radius: 8px;
    font-size: 0.75rem;
    
    &.removable {
      background-color: #dbeafe;
      color: #1e40af;
      display: flex;
      align-items: center;
      gap: 4px;
      
      .remove-capability {
        background: none;
        border: none;
        color: #ef4444;
        cursor: pointer;
        padding: 0;
        font-size: 0.7rem;
        
        &:hover {
          color: #dc2626;
        }
      }
    }
  }
  
  .more-capabilities {
    color: $text-muted;
    font-size: 0.75rem;
    font-style: italic;
  }
}

.pubsub-topic {
  .topic-code {
    background-color: #f3f4f6;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-family: monospace;
  }
}

.created-time {
  font-size: 0.875rem;
  color: $text-muted;
  min-width: 120px;
}

.actions-cell {
  .action-btn {
    padding: 6px 8px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    margin-right: 4px;
    font-size: 0.75rem;
    
    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    
    &.view-btn {
      background-color: #3b82f6;
      color: white;
      
      &:hover {
        background-color: #2563eb;
      }
    }
    
    &.edit-btn {
      background-color: #f59e0b;
      color: white;
      
      &:hover:not(:disabled) {
        background-color: #d97706;
      }
    }
    
    &.activate-btn {
      background-color: #10b981;
      color: white;
      
      &:hover:not(:disabled) {
        background-color: #059669;
      }
    }
    
    &.deactivate-btn {
      background-color: #6b7280;
      color: white;
      
      &:hover:not(:disabled) {
        background-color: #4b5563;
      }
    }
    
    &.delete-btn {
      background-color: #ef4444;
      color: white;
      
      &:hover:not(:disabled) {
        background-color: #dc2626;
      }
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
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  width: 90%;
  
  &.large-modal {
    max-width: 800px;
  }
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

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: $spacing-md;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.form-group {
  margin-bottom: $spacing-lg;
  
  label {
    display: block;
    font-weight: 600;
    margin-bottom: $spacing-sm;
    color: $text-primary;
  }
  
  .form-input, .form-textarea {
    width: 100%;
    padding: $spacing-md;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 0.875rem;
    
    &:focus {
      outline: none;
      border-color: #3b82f6;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
  }
  
  .form-textarea {
    resize: vertical;
    min-height: 80px;
  }
  
  .form-help {
    display: block;
    margin-top: $spacing-xs;
    color: $text-muted;
    font-size: 0.75rem;
  }
}

.capabilities-input {
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: $spacing-sm;
  
  .selected-capabilities {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-bottom: $spacing-sm;
    min-height: 24px;
  }
  
  .add-capability {
    display: flex;
    gap: $spacing-sm;
    
    .capability-input {
      flex: 1;
      padding: $spacing-sm;
      border: 1px solid #e5e7eb;
      border-radius: 4px;
      font-size: 0.875rem;
      
      &:focus {
        outline: none;
        border-color: #3b82f6;
      }
    }
    
    .add-capability-btn {
      background-color: #10b981;
      color: white;
      border: none;
      padding: $spacing-sm;
      border-radius: 4px;
      cursor: pointer;
      
      &:hover {
        background-color: #059669;
      }
    }
  }
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: $spacing-sm;
  margin-top: $spacing-xl;
  
  .cancel-btn {
    background: none;
    border: 1px solid #d1d5db;
    padding: $spacing-md $spacing-lg;
    border-radius: 6px;
    cursor: pointer;
    color: $text-muted;
    
    &:hover {
      background-color: #f9fafb;
    }
  }
  
  .submit-btn {
    background-color: #3b82f6;
    color: white;
    border: none;
    padding: $spacing-md $spacing-lg;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    
    &:disabled {
      opacity: 0.7;
      cursor: not-allowed;
    }
    
    &:hover:not(:disabled) {
      background-color: #2563eb;
    }
  }
}
</style>

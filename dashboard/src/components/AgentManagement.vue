<template>
  <div class="agent-management">
    <div class="agent-header">
      <h2 class="section-title">
        <i class="fas fa-users"></i>
        {{ $t('agents.title') }}
      </h2>
      <p class="section-subtitle">{{ $t('agents.subtitle') }}</p>
      <button @click="showCreateModal = true" class="create-btn">
        <i class="fas fa-plus"></i>
        {{ $t('agents.createButton') }}
      </button>
    </div>

    <!-- 功能開發中警示區塊 -->
    <div class="development-notice">
      <div class="notice-header">
        <i class="fas fa-construction"></i>
        <h3>{{ $t('agents.developmentNotice.title') }}</h3>
      </div>
      <div class="notice-content">
        <p class="notice-intro">{{ $t('agents.developmentNotice.intro') }}</p>
        <div class="features-list">
          <div class="feature-item">
            <i class="fas fa-robot"></i>
            <div class="feature-content">
              <h4>{{ $t('agents.developmentNotice.features.onboarding.title') }}</h4>
              <p>{{ $t('agents.developmentNotice.features.onboarding.description') }}</p>
            </div>
          </div>
          <div class="feature-item">
            <i class="fas fa-rocket"></i>
            <div class="feature-content">
              <h4>{{ $t('agents.developmentNotice.features.provisioning.title') }}</h4>
              <p>{{ $t('agents.developmentNotice.features.provisioning.description') }}</p>
            </div>
          </div>
          <div class="feature-item">
            <i class="fas fa-broadcast-tower"></i>
            <div class="feature-content">
              <h4>{{ $t('agents.developmentNotice.features.registration.title') }}</h4>
              <p>{{ $t('agents.developmentNotice.features.registration.description') }}</p>
            </div>
          </div>
          <div class="feature-item">
            <i class="fas fa-handshake"></i>
            <div class="feature-content">
              <h4>{{ $t('agents.developmentNotice.features.delegation.title') }}</h4>
              <p>{{ $t('agents.developmentNotice.features.delegation.description') }}</p>
            </div>
          </div>
          <div class="feature-item">
            <i class="fas fa-shield-alt"></i>
            <div class="feature-content">
              <h4>{{ $t('agents.developmentNotice.features.guardrails.title') }}</h4>
              <p>{{ $t('agents.developmentNotice.features.guardrails.description') }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="stats-overview">
      <div class="stat-card">
        <div class="stat-value">{{ totalAgents }}</div>
        <div class="stat-label">{{ $t('agents.stats.total') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ activeAgents }}</div>
        <div class="stat-label">{{ $t('agents.stats.active') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ creatingAgents }}</div>
        <div class="stat-label">{{ $t('agents.stats.creating') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ failedAgents }}</div>
        <div class="stat-label">{{ $t('agents.stats.failed') }}</div>
      </div>
    </div>

    <div class="agent-table-container">
      <div class="table-header">
        <h3>{{ $t('agents.table.title') }}</h3>
        <div class="table-controls">
          <select v-model="statusFilter" class="filter-select">
            <option value="">{{ $t('agents.table.allStatus') }}</option>
            <option value="ACTIVE">{{ $t('agents.status.active') }}</option>
            <option value="INACTIVE">{{ $t('agents.status.inactive') }}</option>
            <option value="CREATING">{{ $t('agents.status.creating') }}</option>
            <option value="FAILED">{{ $t('agents.status.failed') }}</option>
          </select>
        </div>
      </div>

      <div class="table-wrapper">
        <table class="agent-table">
          <thead>
            <tr>
              <th>{{ $t('agents.table.name') }}</th>
              <th>{{ $t('agents.table.description') }}</th>
              <th>{{ $t('agents.table.status') }}</th>
              <th>{{ $t('agents.table.capabilities') }}</th>
              <th>{{ $t('agents.table.topic') }}</th>
              <th>{{ $t('agents.table.created') }}</th>
              <th>{{ $t('agents.table.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="agent in filteredAgents" :key="agent.agent_id" :class="getRowClass(agent.status)">
              <td class="agent-name">
                <div class="name-content">
                  <i class="fas fa-robot agent-icon"></i>
                  <span class="name-text">{{ getDisplayName(agent.name) }}</span>
                  <span v-if="isSystemAgent(agent.name)" class="system-badge">{{ $t('common.system') }}</span>
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
                  :title="$t('agents.actions.viewDetails')"
                >
                  <i class="fas fa-eye"></i>
                  {{ $t('agents.actions.viewDetails') }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div v-if="showCreateModal" class="modal-overlay" @click="closeCreateModal">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h3>{{ $t('agents.create.title') }}</h3>
          <button @click="closeCreateModal" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="submitCreateAgent">
            <div class="form-row">
              <div class="form-group">
                <label for="agent-name">{{ $t('agents.create.name') }} *</label>
                <input 
                  id="agent-name"
                  v-model="createForm.name" 
                  type="text" 
                  :placeholder="$t('agents.create.namePlaceholder')"
                  required
                  class="form-input"
                />
              </div>
              <div class="form-group">
                <label for="pubsub-topic">{{ $t('agents.create.pubsubTopic') }}</label>
                <input 
                  id="pubsub-topic"
                  v-model="createForm.pubsub_topic" 
                  type="text" 
                  :placeholder="$t('agents.create.pubsubTopicPlaceholder')"
                  class="form-input"
                />
                <small class="form-help">{{ $t('agents.create.pubsubTopicHelp') }}</small>
              </div>
            </div>

            <div class="form-group">
              <label for="agent-description">{{ $t('agents.create.description') }} *</label>
              <textarea 
                id="agent-description"
                v-model="createForm.description" 
                :placeholder="$t('agents.create.descriptionPlaceholder')"
                required
                class="form-textarea"
                rows="3"
              ></textarea>
            </div>

            <div class="form-group">
              <label for="capabilities">{{ $t('agents.create.capabilities') }}</label>
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
                    :placeholder="$t('agents.create.capabilityPlaceholder')"
                    class="capability-input"
                  />
                  <button type="button" @click="addCapability" class="add-capability-btn">
                    <i class="fas fa-plus"></i>
                  </button>
                </div>
              </div>
              <small class="form-help">{{ $t('agents.create.capabilityHelp') }}</small>
            </div>

            <div class="form-group">
              <label for="system-prompt">{{ $t('agents.create.systemPrompt') }} *</label>
              <textarea 
                id="system-prompt"
                v-model="createForm.system_prompt" 
                :placeholder="$t('agents.create.systemPromptPlaceholder')"
                required
                class="form-textarea"
                rows="8"
              ></textarea>
              <small class="form-help">{{ $t('agents.create.systemPromptHelp') }}</small>
            </div>

            <div class="form-actions">
              <button type="button" @click="closeCreateModal" class="cancel-btn">{{ $t('common.cancel') }}</button>
              <button type="submit" :disabled="submitting" class="submit-btn">
                <i v-if="submitting" class="fas fa-spinner fa-spin"></i>
                {{ submitting ? $t('agents.create.creating') : $t('agents.create.submit') }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- 代理人詳情模態框 -->
    <div v-if="selectedAgent" class="modal-overlay" @click="closeDetailsModal">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h3>{{ $t('agents.details.title') }} - {{ getDisplayName(selectedAgent.name) }}</h3>
          <button @click="closeDetailsModal" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <div class="agent-details">
            <div class="detail-section">
              <h4>{{ $t('agents.details.basicInfo') }}</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>{{ $t('agents.details.name') }}</label>
                  <div class="detail-value">
                    <i class="fas fa-robot agent-icon"></i>
                    <span>{{ getDisplayName(selectedAgent.name) }}</span>
                    <span v-if="isSystemAgent(selectedAgent.name)" class="system-badge">{{ $t('common.system') }}</span>
                  </div>
                </div>
                <div class="detail-item">
                  <label>{{ $t('agents.details.status') }}</label>
                  <span :class="['status-badge', getStatusClass(selectedAgent.status)]">
                    {{ getStatusText(selectedAgent.status) }}
                  </span>
                </div>
                <div class="detail-item">
                  <label>{{ $t('agents.details.created') }}</label>
                  <span>{{ formatTime(selectedAgent.created_at) }}</span>
                </div>
                <div class="detail-item">
                  <label>{{ $t('agents.details.pubsubTopic') }}</label>
                  <code class="topic-code">{{ selectedAgent.pubsub_topic || '-' }}</code>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <h4>{{ $t('agents.details.description') }}</h4>
              <div class="description-content">
                {{ selectedAgent.description }}
              </div>
            </div>

            <div class="detail-section">
              <h4>{{ $t('agents.details.capabilities') }}</h4>
              <div class="capabilities-list">
                <span 
                  v-for="capability in selectedAgent.capabilities" 
                  :key="capability"
                  class="capability-tag"
                >
                  {{ capability }}
                </span>
              </div>
            </div>

            <div v-if="selectedAgent.system_prompt" class="detail-section">
              <h4>{{ $t('agents.details.systemPrompt') }}</h4>
              <div class="system-prompt-content">
                <pre>{{ selectedAgent.system_prompt }}</pre>
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
import { useI18n } from 'vue-i18n'
import type { Agent } from '@/types/agent'

interface Props {
  agents: Agent[]
}

const { t } = useI18n()
const props = defineProps<Props>()
const emit = defineEmits<{
  refresh: []
}>()

const statusFilter = ref('')
const showCreateModal = ref(false)
const selectedAgent = ref<Agent | null>(null)
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

// Display name mapping for system agents
const getDisplayName = (name: string) => {
  const nameMap: Record<string, string> = {
    'ProxyAgent': 'Customer Service Agent',
    'OrchestratorAgent': 'Orchestrator Agent'
  }
  return nameMap[name] || name
}

// Check if agent is a system agent
const isSystemAgent = (name: string) => {
  return name === 'OrchestratorAgent' || name === 'ProxyAgent'
}

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
  const statusKey = status.toLowerCase()
  return t(`agents.status.${statusKey}`) || status
}

const truncateText = (text: string, maxLength: number) => {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

const formatTime = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleString('zh-TW')
}

// Agent operation functions
const viewAgentDetails = (agent: Agent) => {
  selectedAgent.value = agent
}

const closeDetailsModal = () => {
  selectedAgent.value = null
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

// 功能開發中警示區塊樣式
.development-notice {
  background: linear-gradient(135deg, #fee2e2, #fecaca);
  border: 2px solid #ef4444;
  border-radius: 12px;
  padding: $spacing-xl;
  margin-bottom: $spacing-xl;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.15);

  .notice-header {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    margin-bottom: $spacing-lg;

    i {
      font-size: 1.5rem;
      color: #dc2626;
      animation: pulse 2s infinite;
    }

    h3 {
      margin: 0;
      color: #dc2626;
      font-size: 1.25rem;
      font-weight: 700;
    }
  }

  .notice-content {
    .notice-intro {
      color: #7f1d1d;
      font-size: 0.95rem;
      line-height: 1.6;
      margin-bottom: $spacing-lg;
      font-weight: 500;
    }

    .features-list {
      display: grid;
      gap: $spacing-lg;

      .feature-item {
        display: flex;
        gap: $spacing-md;
        align-items: flex-start;
        background: rgba(255, 255, 255, 0.7);
        padding: $spacing-md;
        border-radius: 8px;
        border-left: 4px solid #dc2626;

        i {
          font-size: 1.2rem;
          color: #dc2626;
          margin-top: 2px;
          flex-shrink: 0;
        }

        .feature-content {
          h4 {
            margin: 0 0 $spacing-sm 0;
            color: #991b1b;
            font-size: 0.95rem;
            font-weight: 600;
          }

          p {
            margin: 0;
            color: #7f1d1d;
            font-size: 0.875rem;
            line-height: 1.5;
          }
        }
      }
    }
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.agent-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: $spacing-xl;
  flex-wrap: wrap;
  gap: $spacing-md;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: $text-primary;
  margin: 0;
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  
  i {
    color: #3b82f6;
  }
}

.section-subtitle {
  color: $text-muted;
  font-size: 0.875rem;
  margin: $spacing-xs 0 0 0;
  flex-basis: 100%;
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
  min-width: 800px;
  
  th, td {
    padding: $spacing-md;
    text-align: left;
    border-bottom: 1px solid #f3f4f6;
  }
  
  // Set minimum widths for columns
  th:nth-child(1), td:nth-child(1) { min-width: 180px; } // Name
  th:nth-child(2), td:nth-child(2) { min-width: 200px; } // Description  
  th:nth-child(3), td:nth-child(3) { min-width: 100px; } // Status
  th:nth-child(4), td:nth-child(4) { min-width: 150px; } // Capabilities
  th:nth-child(5), td:nth-child(5) { min-width: 120px; } // Topic
  th:nth-child(6), td:nth-child(6) { min-width: 120px; } // Created
  th:nth-child(7), td:nth-child(7) { min-width: 120px; } // Actions
  
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
  white-space: nowrap;
  display: inline-block;
  
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

// 代理人詳情樣式
.agent-details {
  .detail-section {
    margin-bottom: $spacing-xl;
    
    h4 {
      font-size: 1.1rem;
      font-weight: 600;
      color: $text-primary;
      margin-bottom: $spacing-md;
      padding-bottom: $spacing-sm;
      border-bottom: 2px solid #e5e7eb;
    }
  }
  
  .detail-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: $spacing-md;
    
    .detail-item {
      label {
        display: block;
        font-weight: 600;
        color: $text-secondary;
        margin-bottom: $spacing-xs;
        font-size: 0.875rem;
      }
      
      .detail-value {
        display: flex;
        align-items: center;
        gap: $spacing-sm;
        
        .agent-icon {
          color: #3b82f6;
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
      
      .topic-code {
        background-color: #f3f4f6;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-family: monospace;
      }
    }
  }
  
  .description-content {
    background-color: #f9fafb;
    padding: $spacing-md;
    border-radius: 8px;
    color: $text-primary;
    line-height: 1.6;
    border-left: 4px solid #3b82f6;
  }
  
  .capabilities-list {
    display: flex;
    flex-wrap: wrap;
    gap: $spacing-sm;
    
    .capability-tag {
      background-color: #dbeafe;
      color: #1e40af;
      padding: 4px 12px;
      border-radius: 16px;
      font-size: 0.875rem;
      font-weight: 500;
    }
  }
  
  .system-prompt-content {
    background-color: #f3f4f6;
    border-radius: 8px;
    padding: $spacing-md;
    border: 1px solid #d1d5db;
    
    pre {
      margin: 0;
      font-size: 0.875rem;
      color: $text-primary;
      white-space: pre-wrap;
      word-break: break-word;
      line-height: 1.5;
      font-family: 'Courier New', monospace;
    }
  }
}
</style>

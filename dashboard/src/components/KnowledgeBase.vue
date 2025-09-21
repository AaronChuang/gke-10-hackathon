<template>
  <div class="knowledge-base">
    <div class="kb-header">
      <h2 class="section-title">知識庫管理</h2>
      <button @click="showAddModal = true" class="add-btn">
        <i class="fas fa-plus"></i>
        索引新網站
      </button>
    </div>

    <div class="stats-overview">
      <div class="stat-card">
        <div class="stat-value">{{ totalEntries }}</div>
        <div class="stat-label">總網站數</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ activeEntries }}</div>
        <div class="stat-label">活躍索引</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ totalIndexedPages }}</div>
        <div class="stat-label">已索引頁面</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ processingEntries }}</div>
        <div class="stat-label">處理中</div>
      </div>
    </div>

    <div class="kb-table-container">
      <div class="table-header">
        <h3>知識庫列表</h3>
        <div class="table-controls">
          <select v-model="statusFilter" class="filter-select">
            <option value="">所有狀態</option>
            <option value="QUEUED">排隊中</option>
            <option value="CRAWLING">爬取中</option>
            <option value="INDEXING">索引中</option>
            <option value="ACTIVE">活躍</option>
            <option value="FAILED">失敗</option>
          </select>
          <button @click="refreshData" class="refresh-btn">
            <i class="fas fa-sync-alt"></i>
            刷新
          </button>
        </div>
      </div>

      <div class="table-wrapper">
        <table class="kb-table">
          <thead>
            <tr>
              <th>網站 URL</th>
              <th>狀態</th>
              <th>進度</th>
              <th>索引頁面</th>
              <th>創建時間</th>
              <th>最後更新</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="entry in filteredEntries" :key="entry.kb_id" :class="getRowClass(entry.status)">
              <td class="url-cell">
                <div class="url-content">
                  <a :href="entry.url" target="_blank" class="url-link">
                    {{ truncateUrl(entry.url) }}
                  </a>
                  <i class="fas fa-external-link-alt external-icon"></i>
                </div>
              </td>
              <td>
                <span :class="['status-badge', getStatusClass(entry.status)]">
                  {{ getStatusText(entry.status) }}
                </span>
              </td>
              <td class="progress-cell">
                <div class="progress-container">
                  <div class="progress-bar">
                    <div 
                      class="progress-fill" 
                      :style="{ width: getProgressPercentage(entry) + '%' }"
                      :class="getProgressClass(entry.status)"
                    ></div>
                  </div>
                  <span class="progress-text">{{ getProgressPercentage(entry) }}%</span>
                </div>
              </td>
              <td class="pages-cell">
                <div class="pages-info">
                  <span class="pages-count">{{ entry.indexed_pages.toLocaleString() }}</span>
                  <span v-if="entry.total_pages > 0" class="pages-total">
                    / {{ entry.total_pages.toLocaleString() }}
                  </span>
                </div>
              </td>
              <td class="time-cell">{{ formatTime(entry.created_at) }}</td>
              <td class="time-cell">{{ formatTime(entry.updated_at) }}</td>
              <td class="actions-cell">
                <button 
                  @click="viewEntryDetails(entry)" 
                  class="action-btn view-btn"
                  title="查看詳情"
                >
                  <i class="fas fa-eye"></i>
                </button>
                <button 
                  @click="deleteEntry(entry)" 
                  :disabled="entry.status === 'CRAWLING' || entry.status === 'INDEXING'"
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

    <!-- 添加網站模態框 -->
    <div v-if="showAddModal" class="modal-overlay" @click="closeAddModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>索引新網站</h3>
          <button @click="closeAddModal" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="submitNewWebsite">
            <div class="form-group">
              <label for="website-url">網站 URL</label>
              <input 
                id="website-url"
                v-model="newWebsiteUrl" 
                type="url" 
                placeholder="https://example.com"
                required
                class="form-input"
              />
              <small class="form-help">請輸入完整的網站 URL，系統將自動爬取並索引網站內容</small>
            </div>
            <div class="form-actions">
              <button type="button" @click="closeAddModal" class="cancel-btn">取消</button>
              <button type="submit" :disabled="submitting" class="submit-btn">
                <i v-if="submitting" class="fas fa-spinner fa-spin"></i>
                {{ submitting ? '提交中...' : '開始索引' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- 詳情模態框 -->
    <div v-if="selectedEntry" class="modal-overlay" @click="closeDetailsModal">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h3>知識庫詳情</h3>
          <button @click="closeDetailsModal" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <div class="detail-section">
            <h4>基本信息</h4>
            <div class="detail-grid">
              <div class="detail-item">
                <label>網站 URL:</label>
                <a :href="selectedEntry.url" target="_blank" class="url-link">
                  {{ selectedEntry.url }}
                </a>
              </div>
              <div class="detail-item">
                <label>狀態:</label>
                <span :class="['status-badge', getStatusClass(selectedEntry.status)]">
                  {{ getStatusText(selectedEntry.status) }}
                </span>
              </div>
              <div class="detail-item">
                <label>創建時間:</label>
                <span>{{ formatTime(selectedEntry.created_at) }}</span>
              </div>
              <div class="detail-item">
                <label>最後更新:</label>
                <span>{{ formatTime(selectedEntry.updated_at) }}</span>
              </div>
            </div>
          </div>

          <div class="detail-section">
            <h4>索引統計</h4>
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-number">{{ selectedEntry.indexed_pages.toLocaleString() }}</div>
                <div class="stat-description">已索引頁面</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">{{ selectedEntry.total_pages.toLocaleString() }}</div>
                <div class="stat-description">總發現頁面</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">{{ getProgressPercentage(selectedEntry) }}%</div>
                <div class="stat-description">完成進度</div>
              </div>
            </div>
          </div>

          <div v-if="selectedEntry.error_message" class="detail-section">
            <h4>錯誤信息</h4>
            <div class="error-message">
              {{ selectedEntry.error_message }}
            </div>
          </div>

          <div v-if="selectedEntry.metadata && Object.keys(selectedEntry.metadata).length > 0" class="detail-section">
            <h4>元數據</h4>
            <div class="metadata-content">
              <pre>{{ JSON.stringify(selectedEntry.metadata, null, 2) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { KnowledgeEntry } from '@/types/knowledge'

interface Props {
  knowledgeEntries: KnowledgeEntry[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  refresh: []
}>()

const statusFilter = ref('')
const showAddModal = ref(false)
const selectedEntry = ref<KnowledgeEntry | null>(null)
const newWebsiteUrl = ref('')
const submitting = ref(false)

const filteredEntries = computed(() => {
  if (!statusFilter.value) return props.knowledgeEntries
  return props.knowledgeEntries.filter(entry => entry.status === statusFilter.value)
})

const totalEntries = computed(() => props.knowledgeEntries.length)
const activeEntries = computed(() => props.knowledgeEntries.filter(e => e.status === 'ACTIVE').length)
const totalIndexedPages = computed(() => props.knowledgeEntries.reduce((sum, e) => sum + e.indexed_pages, 0))
const processingEntries = computed(() => 
  props.knowledgeEntries.filter(e => e.status === 'CRAWLING' || e.status === 'INDEXING').length
)

const getRowClass = (status: string) => {
  if (status === 'CRAWLING' || status === 'INDEXING') return 'processing-row'
  if (status === 'ACTIVE') return 'active-row'
  if (status === 'FAILED') return 'failed-row'
  return ''
}

const getStatusClass = (status: string) => {
  switch (status) {
    case 'QUEUED': return 'status-queued'
    case 'CRAWLING': return 'status-crawling'
    case 'INDEXING': return 'status-indexing'
    case 'ACTIVE': return 'status-active'
    case 'FAILED': return 'status-failed'
    default: return 'status-unknown'
  }
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'QUEUED': '排隊中',
    'CRAWLING': '爬取中',
    'INDEXING': '索引中',
    'ACTIVE': '活躍',
    'FAILED': '失敗'
  }
  return statusMap[status] || status
}

const getProgressPercentage = (entry: KnowledgeEntry) => {
  if (entry.total_pages === 0) return 0
  return Math.round((entry.indexed_pages / entry.total_pages) * 100)
}

const getProgressClass = (status: string) => {
  switch (status) {
    case 'CRAWLING': return 'progress-crawling'
    case 'INDEXING': return 'progress-indexing'
    case 'ACTIVE': return 'progress-completed'
    case 'FAILED': return 'progress-failed'
    default: return 'progress-pending'
  }
}

const truncateUrl = (url: string) => {
  if (url.length <= 50) return url
  return url.substring(0, 47) + '...'
}

const formatTime = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleString('zh-TW')
}

const refreshData = () => {
  emit('refresh')
}

const submitNewWebsite = async () => {
  if (!newWebsiteUrl.value) return
  
  submitting.value = true
  try {
    // 這裡應該調用 useKnowledgeBase 的 indexWebsite 方法
    // 為了簡化，我們直接發送 API 請求
    const response = await fetch('/api/knowledge-base/index', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url: newWebsiteUrl.value })
    })

    if (response.ok) {
      closeAddModal()
      emit('refresh')
    } else {
      const error = await response.json()
      alert(`索引失敗: ${error.detail || '未知錯誤'}`)
    }
  } catch (error) {
    alert(`索引失敗: ${error}`)
  } finally {
    submitting.value = false
  }
}


const deleteEntry = async (entry: KnowledgeEntry) => {
  if (confirm(`確定要刪除 ${entry.url} 的索引嗎？此操作無法復原。`)) {
    try {
      const response = await fetch(`/api/knowledge-base/${entry.kb_id}`, {
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

const viewEntryDetails = (entry: KnowledgeEntry) => {
  selectedEntry.value = entry
}

const closeAddModal = () => {
  showAddModal.value = false
  newWebsiteUrl.value = ''
  submitting.value = false
}

const closeDetailsModal = () => {
  selectedEntry.value = null
}
</script>

<style lang="scss" scoped>
.knowledge-base {
  padding: $spacing-lg;
}

.kb-header {
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

.add-btn {
  background-color: #10b981;
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
    background-color: #059669;
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
    color: #10b981;
    margin-bottom: $spacing-xs;
  }
  
  .stat-label {
    color: $text-muted;
    font-size: 0.875rem;
  }
}

.kb-table-container {
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

.kb-table {
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
  
  .processing-row {
    background-color: #fef3c7;
  }
  
  .active-row {
    background-color: #d1fae5;
  }
  
  .failed-row {
    background-color: #fee2e2;
  }
}

.url-cell {
  max-width: 300px;
  
  .url-content {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
  }
  
  .url-link {
    color: #3b82f6;
    text-decoration: none;
    font-size: 0.875rem;
    
    &:hover {
      text-decoration: underline;
    }
  }
  
  .external-icon {
    color: $text-muted;
    font-size: 0.75rem;
  }
}

.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  
  &.status-queued {
    background-color: #f3f4f6;
    color: #6b7280;
  }
  
  &.status-crawling {
    background-color: #dbeafe;
    color: #1d4ed8;
  }
  
  &.status-indexing {
    background-color: #fbbf24;
    color: #92400e;
  }
  
  &.status-active {
    background-color: #10b981;
    color: white;
  }
  
  &.status-failed {
    background-color: #ef4444;
    color: white;
  }
}

.progress-cell {
  min-width: 120px;
  
  .progress-container {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
  }
  
  .progress-bar {
    flex: 1;
    height: 8px;
    background-color: #f3f4f6;
    border-radius: 4px;
    overflow: hidden;
  }
  
  .progress-fill {
    height: 100%;
    transition: width 0.3s ease;
    
    &.progress-pending {
      background-color: #d1d5db;
    }
    
    &.progress-crawling {
      background-color: #3b82f6;
    }
    
    &.progress-indexing {
      background-color: #f59e0b;
    }
    
    &.progress-completed {
      background-color: #10b981;
    }
    
    &.progress-failed {
      background-color: #ef4444;
    }
  }
  
  .progress-text {
    font-size: 0.75rem;
    color: $text-muted;
    min-width: 35px;
  }
}

.pages-cell {
  .pages-info {
    font-size: 0.875rem;
    
    .pages-count {
      font-weight: 600;
    }
    
    .pages-total {
      color: $text-muted;
    }
  }
}

.time-cell {
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
    
    &.reindex-btn {
      background-color: #f59e0b;
      color: white;
      
      &:hover:not(:disabled) {
        background-color: #d97706;
      }
    }
    
    &.view-btn {
      background-color: #3b82f6;
      color: white;
      
      &:hover {
        background-color: #2563eb;
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
  max-width: 500px;
  max-height: 80vh;
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

.form-group {
  margin-bottom: $spacing-lg;
  
  label {
    display: block;
    font-weight: 600;
    margin-bottom: $spacing-sm;
    color: $text-primary;
  }
  
  .form-input {
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
  
  .form-help {
    display: block;
    margin-top: $spacing-xs;
    color: $text-muted;
    font-size: 0.75rem;
  }
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: $spacing-sm;
  
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
    background-color: #10b981;
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
      background-color: #059669;
    }
  }
}

// 詳情模態框特定樣式
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
  
  span, a {
    font-size: 0.875rem;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: $spacing-md;
  
  .stat-item {
    text-align: center;
    padding: $spacing-md;
    background-color: #f9fafb;
    border-radius: 6px;
    
    .stat-number {
      font-size: 1.5rem;
      font-weight: 700;
      color: #10b981;
      margin-bottom: $spacing-xs;
    }
    
    .stat-description {
      color: $text-muted;
      font-size: 0.875rem;
    }
  }
}

.error-message {
  background-color: #fee2e2;
  color: #dc2626;
  padding: $spacing-md;
  border-radius: 6px;
  font-size: 0.875rem;
}

.metadata-content {
  background-color: #f9fafb;
  padding: $spacing-md;
  border-radius: 6px;
  
  pre {
    margin: 0;
    font-size: 0.75rem;
    color: $text-primary;
    white-space: pre-wrap;
    word-break: break-word;
  }
}
</style>

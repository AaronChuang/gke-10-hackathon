<template>
  <div class="knowledge-base">
    <div class="kb-header">
      <h2 class="section-title">{{ $t('knowledge.title') }}</h2>
      <button @click="showAddModal = true" class="add-btn">
        <i class="fas fa-plus"></i>
        {{ $t('knowledge.addButton') }}
      </button>
    </div>

    <div class="stats-overview">
      <div class="stat-card">
        <div class="stat-value">{{ totalEntries }}</div>
        <div class="stat-label">{{ $t('knowledge.stats.total') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ activeEntries }}</div>
        <div class="stat-label">{{ $t('knowledge.stats.active') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ totalIndexedPages }}</div>
        <div class="stat-label">{{ $t('knowledge.stats.indexed') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ processingEntries }}</div>
        <div class="stat-label">{{ $t('knowledge.stats.processing') }}</div>
      </div>
    </div>

    <div class="kb-table-container">
      <div class="table-header">
        <h3>{{ $t('knowledge.table.title') }}</h3>
        <div class="table-controls">
          <select v-model="statusFilter" class="filter-select">
            <option value="">{{ $t('knowledge.table.allStatus') }}</option>
            <option value="QUEUED">{{ $t('knowledge.status.queued') }}</option>
            <option value="CRAWLING">{{ $t('knowledge.status.crawling') }}</option>
            <option value="INDEXING">{{ $t('knowledge.status.indexing') }}</option>
            <option value="ACTIVE">{{ $t('knowledge.status.active') }}</option>
            <option value="FAILED">{{ $t('knowledge.status.failed') }}</option>
          </select>
          <button @click="refreshData" class="refresh-btn">
            <i class="fas fa-sync-alt"></i>
            {{ $t('knowledge.table.refresh') }}
          </button>
        </div>
      </div>

      <div class="table-wrapper">
        <table class="kb-table">
          <thead>
            <tr>
              <th>{{ $t('knowledge.table.url') }}</th>
              <th>{{ $t('knowledge.table.status') }}</th>
              <th>{{ $t('knowledge.table.progress') }}</th>
              <th>{{ $t('knowledge.table.pages') }}</th>
              <th>{{ $t('knowledge.table.created') }}</th>
              <th>{{ $t('knowledge.table.updated') }}</th>
              <th>{{ $t('knowledge.table.actions') }}</th>
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
                  :title="$t('knowledge.table.view')"
                >
                  <i class="fas fa-eye"></i>
                  {{ $t('knowledge.table.view') }}
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
          <h3>{{ $t('knowledge.modal.add.title') }}</h3>
          <button @click="closeAddModal" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <div class="demo-notice">
            <div class="notice-title">
              <i class="fas fa-info-circle"></i>
              {{ $t('knowledge.modal.add.demoNotice') }}
            </div>
            <p class="notice-description">
              {{ $t('knowledge.modal.add.demoDescription') }}
            </p>
          </div>
          
          <div class="form-group">
            <label for="website-url">{{ $t('knowledge.modal.add.url') }}</label>
            <input 
              id="website-url"
              v-model="newWebsiteUrl" 
              type="url" 
              :placeholder="$t('knowledge.modal.add.urlPlaceholder')"
              disabled
              class="form-input disabled"
            />
            <small class="form-help">{{ $t('knowledge.modal.add.urlHelp') }}</small>
          </div>
          <div class="form-actions">
            <button type="button" @click="closeAddModal" class="cancel-btn">
              {{ $t('knowledge.modal.add.cancel') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 詳情模態框 -->
    <div v-if="selectedEntry" class="modal-overlay" @click="closeDetailsModal">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h3>{{ $t('knowledge.modal.details.title') }}</h3>
          <button @click="closeDetailsModal" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <div class="detail-section">
            <h4>{{ $t('knowledge.modal.details.basicInfo') }}</h4>
            <div class="detail-grid">
              <div class="detail-item">
                <label>{{ $t('knowledge.modal.details.url') }}</label>
                <a :href="selectedEntry.url" target="_blank" class="url-link">
                  {{ selectedEntry.url }}
                </a>
              </div>
              <div class="detail-item">
                <label>{{ $t('knowledge.modal.details.status') }}</label>
                <span :class="['status-badge', getStatusClass(selectedEntry.status)]">
                  {{ getStatusText(selectedEntry.status) }}
                </span>
              </div>
              <div class="detail-item">
                <label>{{ $t('knowledge.modal.details.created') }}</label>
                <span>{{ formatTime(selectedEntry.created_at) }}</span>
              </div>
              <div class="detail-item">
                <label>{{ $t('knowledge.modal.details.updated') }}</label>
                <span>{{ formatTime(selectedEntry.updated_at) }}</span>
              </div>
            </div>
          </div>

          <div class="detail-section">
            <h4>{{ $t('knowledge.modal.details.stats') }}</h4>
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-number">{{ selectedEntry.indexed_pages.toLocaleString() }}</div>
                <div class="stat-description">{{ $t('knowledge.modal.details.indexedPages') }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">{{ selectedEntry.total_pages.toLocaleString() }}</div>
                <div class="stat-description">{{ $t('knowledge.modal.details.totalPages') }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">{{ getProgressPercentage(selectedEntry) }}%</div>
                <div class="stat-description">{{ $t('knowledge.modal.details.progress') }}</div>
              </div>
            </div>
          </div>

          <div v-if="selectedEntry.error_message" class="detail-section">
            <h4>{{ $t('knowledge.modal.details.error') }}</h4>
            <div class="error-message">
              {{ selectedEntry.error_message }}
            </div>
          </div>

          <div v-if="selectedEntry.status === 'ACTIVE'" class="detail-section">
            <h4>{{ $t('knowledge.modal.details.indexedContent') }}</h4>
            <div class="content-section">
              <div class="content-loading" v-if="loadingContent">
                <i class="fas fa-spinner fa-spin"></i>
                {{ $t('knowledge.modal.details.loadingContent') }}
              </div>
              <div v-else-if="indexedContent.length > 0" class="content-list">
                <div 
                  v-for="(content, index) in indexedContent" 
                  :key="index"
                  class="content-item"
                >
                  <div class="content-header">
                    <h5 class="content-title">{{ content.title || $t('knowledge.modal.details.untitledPage') }}</h5>
                    <span class="content-url">{{ content.url }}</span>
                  </div>
                  <div class="content-preview">
                    {{ truncateContent(content.content) }}
                  </div>
                  <div class="content-meta">
                    <span class="content-length">{{ content.content.length }} {{ $t('knowledge.modal.details.characters') }}</span>
                    <span class="content-chunks">{{ content.chunks || 1 }} {{ $t('knowledge.modal.details.chunks') }}</span>
                  </div>
                </div>
              </div>
              <div v-else class="no-content">
                <i class="fas fa-file-alt"></i>
                <p>{{ $t('knowledge.modal.details.noContent') }}</p>
              </div>
            </div>
          </div>

          <div v-if="selectedEntry.metadata && Object.keys(selectedEntry.metadata).length > 0" class="detail-section">
            <h4>{{ $t('knowledge.modal.details.metadata') }}</h4>
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
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useKnowledgeBase } from '@/composables/useKnowledgeBase'
import type { KnowledgeEntry } from '@/types/knowledge'

const { t } = useI18n()
const { knowledgeEntries, loadKnowledgeBase } = useKnowledgeBase()

const statusFilter = ref('')
const showAddModal = ref(false)
const selectedEntry = ref<KnowledgeEntry | null>(null)
const newWebsiteUrl = ref('http://35.236.185.81/')
const submitting = ref(false)
const loadingContent = ref(false)
const indexedContent = ref<any[]>([])

// 在組件掛載時載入知識庫數據
onMounted(() => {
  loadKnowledgeBase()
})

const filteredEntries = computed(() => {
  if (!statusFilter.value) return knowledgeEntries.value
  return knowledgeEntries.value.filter((entry: KnowledgeEntry) => entry.status === statusFilter.value)
})

const totalEntries = computed(() => knowledgeEntries.value.length)
const activeEntries = computed(() => knowledgeEntries.value.filter((e: KnowledgeEntry) => e.status === 'ACTIVE').length)
const totalIndexedPages = computed(() => knowledgeEntries.value.reduce((sum: number, e: KnowledgeEntry) => sum + e.indexed_pages, 0))
const processingEntries = computed(() => 
  knowledgeEntries.value.filter((e: KnowledgeEntry) => e.status === 'CRAWLING' || e.status === 'INDEXING').length
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
    'QUEUED': t('knowledge.status.queued'),
    'CRAWLING': t('knowledge.status.crawling'),
    'INDEXING': t('knowledge.status.indexing'),
    'ACTIVE': t('knowledge.status.active'),
    'FAILED': t('knowledge.status.failed')
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

const truncateContent = (content: string) => {
  if (content.length <= 200) return content
  return content.substring(0, 197) + '...'
}

const formatTime = (timestamp: number) => {
  const locale = t('common.locale')
  return new Date(timestamp * 1000).toLocaleString(locale, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const refreshData = () => {
  loadKnowledgeBase()
}


const loadIndexedContent = async (kbId: string) => {
  loadingContent.value = true
  indexedContent.value = []
  
  try {
    // 從 Firebase 獲取知識庫的 chunks 子集合
    const { collection, getDocs } = await import('firebase/firestore')
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
    const db = getFirestore(app, "gke-10-hackathon")
    
    const chunksRef = collection(db, 'knowledge_base', kbId, 'chunks')
    const chunksSnapshot = await getDocs(chunksRef)
    
    const contentMap = new Map()
    
    chunksSnapshot.forEach((doc) => {
      const data = doc.data()
      const url = data.url || data.source_url || 'Unknown URL'
      
      if (!contentMap.has(url)) {
        contentMap.set(url, {
          url: url,
          title: data.title || data.page_title || '',
          content: '',
          chunks: 0
        })
      }
      
      const existing = contentMap.get(url)
      existing.content += (data.content || data.text || '') + ' '
      existing.chunks += 1
    })
    
    indexedContent.value = Array.from(contentMap.values())
  } catch (err) {
    console.error('Failed to load indexed content:', err)
    indexedContent.value = []
  } finally {
    loadingContent.value = false
  }
}

const viewEntryDetails = (entry: KnowledgeEntry) => {
  selectedEntry.value = entry
  if (entry.status === 'ACTIVE') {
    loadIndexedContent(entry.kb_id)
  }
}

const closeAddModal = () => {
  showAddModal.value = false
  newWebsiteUrl.value = ''
  submitting.value = false
}

const closeDetailsModal = () => {
  selectedEntry.value = null
  indexedContent.value = []
  loadingContent.value = false
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
      display: flex;
      align-items: center;
      gap: $spacing-xs;
      padding: $spacing-sm $spacing-md;
      
      &:hover {
        background-color: #2563eb;
      }
    }
    
  }
}

// Demo notice 樣式
.demo-notice {
  background-color: #e0f2fe;
  border: 1px solid #0288d1;
  border-radius: 8px;
  padding: $spacing-md;
  margin-bottom: $spacing-lg;
  
  .notice-title {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    font-weight: 600;
    color: #0277bd;
    margin-bottom: $spacing-sm;
    
    i {
      color: #0288d1;
    }
  }
  
  .notice-description {
    color: #01579b;
    font-size: 0.875rem;
    line-height: 1.5;
    margin: 0;
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
  width: 90%;
  display: flex;
  flex-direction: column;
  
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
  overflow-y: auto;
  flex: 1;
  min-height: 0;
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
    
    &.disabled {
      background-color: #f9fafb;
      color: #6b7280;
      cursor: not-allowed;
      
      &:focus {
        border-color: #d1d5db;
        box-shadow: none;
      }
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

// 索引內容樣式
.content-section {
  .content-loading {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: $spacing-sm;
    padding: $spacing-xl;
    color: $text-muted;
    
    i {
      animation: spin 1s linear infinite;
    }
  }
  
  .content-list {
    border: 1px solid #e5e7eb;
    border-radius: 6px;
  }
  
  .content-item {
    padding: $spacing-md;
    border-bottom: 1px solid #f3f4f6;
    
    &:last-child {
      border-bottom: none;
    }
    
    .content-header {
      margin-bottom: $spacing-sm;
      
      .content-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: $text-primary;
        margin: 0 0 4px 0;
      }
      
      .content-url {
        font-size: 0.75rem;
        color: #3b82f6;
        text-decoration: none;
        
        &:hover {
          text-decoration: underline;
        }
      }
    }
    
    .content-preview {
      font-size: 0.75rem;
      color: $text-muted;
      line-height: 1.4;
      margin-bottom: $spacing-sm;
      background-color: #f9fafb;
      padding: $spacing-sm;
      border-radius: 4px;
    }
    
    .content-meta {
      display: flex;
      gap: $spacing-md;
      font-size: 0.75rem;
      color: $text-muted;
      
      .content-length,
      .content-chunks {
        display: flex;
        align-items: center;
        gap: 4px;
      }
    }
  }
  
  .no-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: $spacing-xl;
    color: $text-muted;
    
    i {
      font-size: 2rem;
      margin-bottom: $spacing-sm;
      opacity: 0.5;
    }
    
    p {
      margin: 0;
      font-size: 0.875rem;
    }
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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

<template>
  <div class="chat-test-container">
    <div class="chat-header">
      <h2 class="text-2xl font-bold text-gray-800 mb-4">
        <i class="fas fa-comments mr-2 text-blue-600"></i>
        AI Agent 對話測試
      </h2>
      <p class="text-gray-600 mb-6">與 AI 代理人進行即時對話測試</p>
    </div>

    <!-- Agent 選擇 -->
    <div class="agent-selector mb-6">
      <label class="block text-sm font-medium text-gray-700 mb-2">選擇代理人</label>
      <select 
        v-model="selectedAgent" 
        class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      >
        <option value="">請選擇代理人</option>
        <option value="orchestrator">Orchestrator (智能協調)</option>
        <option value="proxy">Proxy Agent (對話代理)</option>
        <option value="omni">Omni Agent (全能代理)</option>
      </select>
    </div>

    <!-- 對話區域 -->
    <div class="chat-area">
      <div class="messages-container" ref="messagesContainer">
        <div 
          v-for="message in messages" 
          :key="message.id"
          :class="['message', message.type === 'user' ? 'user-message' : 'agent-message']"
        >
          <div class="message-avatar">
            <i :class="message.type === 'user' ? 'fas fa-user' : 'fas fa-robot'"></i>
          </div>
          <div class="message-content">
            <div class="message-header">
              <span class="message-sender">{{ message.type === 'user' ? '您' : selectedAgent || 'Agent' }}</span>
              <span class="message-time">{{ formatTime(message.timestamp) }}</span>
            </div>
            <div class="message-text">{{ message.content }}</div>
          </div>
        </div>
        
        <!-- 載入指示器 -->
        <div v-if="isLoading" class="message agent-message">
          <div class="message-avatar">
            <i class="fas fa-robot"></i>
          </div>
          <div class="message-content">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 輸入區域 -->
      <div class="input-area">
        <div class="input-container">
          <textarea
            v-model="currentMessage"
            @keydown.enter.prevent="sendMessage"
            placeholder="輸入您的訊息... (按 Enter 發送)"
            class="message-input"
            rows="3"
            :disabled="!selectedAgent || isLoading"
          ></textarea>
          <button 
            @click="sendMessage"
            :disabled="!selectedAgent || !currentMessage.trim() || isLoading"
            class="send-button"
          >
            <i class="fas fa-paper-plane"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- 對話歷史控制 -->
    <div class="chat-controls mt-4">
      <button 
        @click="clearMessages"
        class="clear-button"
      >
        <i class="fas fa-trash mr-2"></i>
        清除對話
      </button>
      <button 
        @click="exportChat"
        class="export-button"
        :disabled="messages.length === 0"
      >
        <i class="fas fa-download mr-2"></i>
        匯出對話
      </button>
    </div>

    <!-- 錯誤訊息 -->
    <div v-if="error" class="error-message mt-4">
      <i class="fas fa-exclamation-triangle mr-2"></i>
      {{ error }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'

interface Message {
  id: string
  type: 'user' | 'agent'
  content: string
  timestamp: Date
}

const selectedAgent = ref('')
const currentMessage = ref('')
const messages = ref<Message[]>([])
const isLoading = ref(false)
const error = ref('')
const messagesContainer = ref<HTMLElement>()

// API 基礎 URL - 根據環境調整
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const sendMessage = async () => {
  if (!selectedAgent.value || !currentMessage.value.trim()) return

  const userMessage: Message = {
    id: Date.now().toString(),
    type: 'user',
    content: currentMessage.value.trim(),
    timestamp: new Date()
  }

  messages.value.push(userMessage)
  const messageToSend = currentMessage.value.trim()
  currentMessage.value = ''
  isLoading.value = true
  error.value = ''

  await scrollToBottom()

  try {
    const endpoint = getAgentEndpoint(selectedAgent.value)
    const response = await fetch(`${endpoint}/api/conversation`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_prompt: messageToSend,
        conversation_id: `chat-test-${Date.now()}`,
        user_id: 'dashboard-user'
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const data = await response.json()
    
    const agentMessage: Message = {
      id: (Date.now() + 1).toString(),
      type: 'agent',
      content: data.response || data.message || '收到回應，但內容為空',
      timestamp: new Date()
    }

    messages.value.push(agentMessage)
    await scrollToBottom()

  } catch (err) {
    error.value = `發送訊息失敗: ${err instanceof Error ? err.message : '未知錯誤'}`
    console.error('Chat error:', err)
  } finally {
    isLoading.value = false
  }
}

const getAgentEndpoint = (agent: string): string => {
  switch (agent) {
    case 'orchestrator':
      return 'http://localhost:8000'
    case 'proxy':
      return 'http://localhost:8001'
    case 'omni':
      return 'http://localhost:8002'
    default:
      return API_BASE_URL
  }
}

const clearMessages = () => {
  messages.value = []
  error.value = ''
}

const exportChat = () => {
  const chatData = {
    agent: selectedAgent.value,
    timestamp: new Date().toISOString(),
    messages: messages.value
  }
  
  const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `chat-${selectedAgent.value}-${new Date().toISOString().split('T')[0]}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const formatTime = (date: Date): string => {
  return date.toLocaleTimeString('zh-TW', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

onMounted(() => {
  // 添加歡迎訊息
  messages.value.push({
    id: 'welcome',
    type: 'agent',
    content: '歡迎使用 AI Agent 對話測試！請選擇一個代理人開始對話。',
    timestamp: new Date()
  })
})
</script>

<style lang="scss" scoped>
.chat-test-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 1.5rem;
}

.chat-header {
  text-align: center;
  margin-bottom: 2rem;
}

.agent-selector {
  select {
    appearance: none;
    background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e");
    background-position: right 0.5rem center;
    background-repeat: no-repeat;
    background-size: 1.5em 1.5em;
    padding-right: 2.5rem;
  }
}

.chat-area {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
  background: white;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.messages-container {
  height: 400px;
  overflow-y: auto;
  padding: 1rem;
  background: #f9fafb;
}

.message {
  display: flex;
  margin-bottom: 1rem;
  
  &.user-message {
    flex-direction: row-reverse;
    
    .message-content {
      background: #3b82f6;
      color: white;
      margin-right: 0.5rem;
    }
    
    .message-avatar {
      background: #3b82f6;
      color: white;
    }
  }
  
  &.agent-message {
    .message-content {
      background: white;
      border: 1px solid #e5e7eb;
      margin-left: 0.5rem;
    }
    
    .message-avatar {
      background: #6b7280;
      color: white;
    }
  }
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message-content {
  max-width: 70%;
  padding: 0.75rem 1rem;
  border-radius: 12px;
  word-wrap: break-word;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
  font-size: 0.75rem;
  opacity: 0.8;
}

.message-sender {
  font-weight: 600;
}

.message-time {
  font-size: 0.7rem;
}

.message-text {
  line-height: 1.5;
}

.typing-indicator {
  display: flex;
  gap: 0.25rem;
  
  span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #6b7280;
    animation: typing 1.4s infinite ease-in-out;
    
    &:nth-child(1) { animation-delay: -0.32s; }
    &:nth-child(2) { animation-delay: -0.16s; }
  }
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.input-area {
  padding: 1rem;
  background: white;
  border-top: 1px solid #e5e7eb;
}

.input-container {
  display: flex;
  gap: 0.75rem;
  align-items: flex-end;
}

.message-input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  resize: none;
  font-family: inherit;
  
  &:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
  
  &:disabled {
    background: #f3f4f6;
    cursor: not-allowed;
  }
}

.send-button {
  padding: 0.75rem 1rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
  
  &:hover:not(:disabled) {
    background: #2563eb;
  }
  
  &:disabled {
    background: #9ca3af;
    cursor: not-allowed;
  }
}

.chat-controls {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.clear-button, .export-button {
  padding: 0.5rem 1rem;
  border: 1px solid #d1d5db;
  background: white;
  color: #374151;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover:not(:disabled) {
    background: #f3f4f6;
    border-color: #9ca3af;
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.clear-button:hover:not(:disabled) {
  color: #dc2626;
  border-color: #dc2626;
}

.error-message {
  padding: 1rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  text-align: center;
}
</style>

<template>
  <div class="chat-test-container">
    <div class="chat-header">
      <h2 class="text-2xl font-bold text-gray-800 mb-4">
        <i class="fas fa-comments mr-2 text-blue-600"></i>
        AI Agent 對話測試
      </h2>
      <p class="text-gray-600 mb-6">與 AI 代理人進行即時對話測試</p>
    </div>

    <!-- 固定使用 Proxy Agent -->
    <div class="agent-info mb-6">
      <div class="agent-card">
        <div class="agent-icon">
          <i class="fa-solid fa-headset"></i>
        </div>
        <div class="agent-details">
          <h3 class="agent-name">Proxy Agent</h3>
          <p class="agent-description">智能對話代理 - 為您提供專業的AI對話服務</p>
        </div>
        <div class="agent-status">
          <span class="status-indicator online"></span>
          <span class="status-text">線上</span>
        </div>
      </div>
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
            <i :class="message.type === 'user' ? 'fa-solid fa-user' : 'fa-solid fa-headset'"></i>
          </div>
          <div class="message-content">
            <div class="message-header">
              <span class="message-sender">{{ message.type === 'user' ? '您' : 'Proxy Agent' }}</span>
              <span class="message-time">{{ formatTime(message.timestamp) }}</span>
            </div>
            <div class="message-text">{{ message.content }}</div>
          </div>
        </div>
        
        <!-- 載入指示器 -->
        <div v-if="isLoading" class="message agent-message">
          <div class="message-avatar">
            <i class="fa-solid fa-headset"></i>
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
            rows="2"
            :disabled="isLoading"
          ></textarea>
          <button 
            @click="sendMessage"
            :disabled="!currentMessage.trim() || isLoading"
            class="send-button"
          >
            <i class="fa-solid fa-paper-plane"></i>
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
        <i class="fa-solid fa-trash mr-2"></i>
        清除對話
      </button>
      <button 
        @click="exportChat"
        class="export-button"
        :disabled="messages.length === 0"
      >
        <i class="fa-solid fa-download mr-2"></i>
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
import { API_URLS } from '@/config/api'

interface Message {
  id: string
  type: 'user' | 'agent'
  content: string
  timestamp: Date
}

// 固定使用 proxy agent，不再需要選擇
const currentMessage = ref('')
const messages = ref<Message[]>([])
const isLoading = ref(false)
const error = ref('')
const messagesContainer = ref<HTMLElement>()

// 現在使用 Vite 代理，不需要直接指定 API URL

const sendMessage = async () => {
  if (!currentMessage.value.trim()) return

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
    // 準備對話歷史，轉換為後端期望的格式
    const conversationHistory = messages.value
      .filter(msg => msg.id !== 'welcome') // 排除歡迎訊息
      .map(msg => ({
        sender: msg.type === 'user' ? 'user' : 'ai',
        text: msg.content
      }))

    // 使用配置的 API URL
    const response = await fetch(API_URLS.CONVERSATION, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: 'dashboard-user',
        user_prompt: messageToSend,
        conversation_history: conversationHistory,
        product_context: null // 可選參數，暫時設為 null
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const data = await response.json()
    
    const agentMessage: Message = {
      id: (Date.now() + 1).toString(),
      type: 'agent',
      content: data.agent_response || '收到回應，但內容為空',
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

// 移除 getAgentEndpoint 函數，因為現在使用 Vite 代理

const clearMessages = () => {
  messages.value = []
  error.value = ''
}

const exportChat = () => {
  const chatData = {
    agent: 'proxy',
    timestamp: new Date().toISOString(),
    messages: messages.value
  }
  
  const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `chat-proxy-${new Date().toISOString().split('T')[0]}.json`
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
    content: '您好！我是 Proxy Agent，很高興為您服務。請輸入您的問題，我會盡力為您解答。',
    timestamp: new Date()
  })
})
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as *;

.chat-test-container {
  max-width: 900px;
  margin: 0 auto;
  padding: $spacing-xl;
  background: $bg-primary;
  min-height: 100vh;
}

.chat-header {
  text-align: center;
  margin-bottom: $spacing-xl;
  
  h2 {
    font-size: $font-3xl;
    font-weight: 700;
    color: $text-primary;
    margin-bottom: $spacing-md;
    
    i {
      color: #3b82f6;
    }
  }
  
  p {
    font-size: $font-lg;
    color: $text-secondary;
  }
}

.agent-info {
  margin-bottom: $spacing-xl;
}

.agent-card {
  display: flex;
  align-items: center;
  padding: $spacing-lg;
  background: $bg-card;
  border-radius: 16px;
  box-shadow: $shadow-md;
  border: 1px solid $bg-accent;
  transition: all $transition-normal;
  
  &:hover {
    box-shadow: $shadow-lg;
    transform: translateY(-2px);
  }
}

.agent-icon {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #60a5fa, #3b82f6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: $spacing-lg;
  
  i {
    font-size: $font-2xl;
    color: white;
  }
}

.agent-details {
  flex: 1;
}

.agent-name {
  font-size: $font-xl;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: $spacing-xs;
}

.agent-description {
  font-size: $font-base;
  color: $text-secondary;
  line-height: 1.6;
}

.agent-status {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  
  &.online {
    background: $status-completed;
    box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
    animation: pulse 2s infinite;
  }
}

.status-text {
  font-size: $font-sm;
  font-weight: 500;
  color: $status-completed;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

.chat-area {
  border: 1px solid $bg-accent;
  border-radius: 20px;
  overflow: hidden;
  background: $bg-card;
  box-shadow: $shadow-lg;
  margin-bottom: $spacing-lg;
}

.messages-container {
  height: 450px;
  overflow-y: auto;
  padding: $spacing-xl;
  background: linear-gradient(to bottom, #f8fafc, #f1f5f9);
  
  &::-webkit-scrollbar {
    width: 8px;
  }
  
  &::-webkit-scrollbar-track {
    background: $bg-accent;
    border-radius: 4px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: $text-light;
    border-radius: 4px;
    
    &:hover {
      background: $text-gray;
    }
  }
}

.message {
  display: flex;
  margin-bottom: $spacing-lg;
  animation: slideIn 0.3s ease-out;
  
  &.user-message {
    flex-direction: row-reverse;
    
    .message-content {
      background: linear-gradient(135deg, #60a5fa, #3b82f6);
      color: white;
      margin-right: $spacing-md;
      border: none;
    }
    
    .message-avatar {
      background: linear-gradient(135deg, #60a5fa, #3b82f6);
      color: white;
    }
  }
  
  &.agent-message {
    .message-content {
      background: $bg-card;
      border: 1px solid $bg-accent;
      margin-left: $spacing-md;
      color: $text-primary;
    }
    
    .message-avatar {
      background: linear-gradient(135deg, #6b7280, #4b5563);
      color: white;
    }
  }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: $shadow-md;
  
  i {
    font-size: $font-lg;
  }
}

.message-content {
  max-width: 75%;
  padding: $spacing-md $spacing-lg;
  border-radius: 18px;
  word-wrap: break-word;
  box-shadow: $shadow-sm;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $spacing-xs;
  font-size: $font-xs;
  opacity: 0.8;
}

.message-sender {
  font-weight: 600;
  font-size: $font-sm;
}

.message-time {
  font-size: $font-xs;
}

.message-text {
  line-height: 1.6;
  font-size: $font-base;
}

.typing-indicator {
  display: flex;
  gap: $spacing-xs;
  padding: $spacing-sm;
  
  span {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: $text-gray;
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
  padding: $spacing-lg;
  background: $bg-card;
  border-top: 1px solid $bg-accent;
}

.input-container {
  display: flex;
  gap: $spacing-md;
  align-items: flex-end;
  padding: $spacing-sm;
}

.message-input {
  flex: 1;
  padding: $spacing-lg;
  border: 2px solid $bg-accent;
  border-radius: 16px;
  resize: none;
  font-family: inherit;
  font-size: $font-base;
  line-height: 1.5;
  background: $bg-card;
  color: $text-primary;
  transition: all $transition-normal;
  min-height: 60px;
  max-height: 120px;
  
  &::placeholder {
    color: $text-muted;
  }
  
  &:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
    background: $bg-card;
  }
  
  &:disabled {
    background: $bg-accent;
    cursor: not-allowed;
    opacity: 0.6;
  }
}

.send-button {
  padding: $spacing-lg;
  background: linear-gradient(135deg, #60a5fa, #3b82f6);
  color: white;
  border: none;
  border-radius: 16px;
  cursor: pointer;
  transition: all $transition-normal;
  box-shadow: $shadow-md;
  font-weight: 500;
  min-width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  
  &:hover:not(:disabled) {
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    transform: translateY(-2px);
    box-shadow: $shadow-lg;
  }
  
  &:disabled {
    background: $text-light;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
  
  i {
    font-size: $font-xl;
  }
}

.chat-controls {
  display: flex;
  gap: $spacing-lg;
  justify-content: center;
  margin-top: $spacing-xl;
  padding: $spacing-md;
}

.clear-button, .export-button {
  padding: $spacing-md $spacing-xl;
  border: 2px solid $bg-accent;
  background: $bg-card;
  color: $text-secondary;
  border-radius: 12px;
  cursor: pointer;
  transition: all $transition-normal;
  font-weight: 500;
  font-size: $font-base;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  
  &:hover:not(:disabled) {
    background: $bg-hover;
    border-color: $text-light;
    transform: translateY(-1px);
    box-shadow: $shadow-sm;
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  i {
    margin-right: $spacing-sm;
  }
}

.clear-button:hover:not(:disabled) {
  color: $status-failed;
  border-color: $status-failed;
}

.export-button:hover:not(:disabled) {
  color: #3b82f6;
  border-color: #3b82f6;
}

.error-message {
  padding: $spacing-lg;
  background: #fef2f2;
  border: 2px solid #fecaca;
  border-radius: 12px;
  color: $status-failed;
  text-align: center;
  font-weight: 500;
  margin-top: $spacing-lg;
  
  i {
    margin-right: $spacing-sm;
  }
}
</style>

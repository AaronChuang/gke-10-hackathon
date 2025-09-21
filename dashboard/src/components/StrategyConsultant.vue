<template>
  <div class="strategy-consultant">
    <div class="header">
      <h2 class="title">
        <i class="fas fa-lightbulb"></i>
        {{ $t('strategy.title') }}
      </h2>
      <p class="subtitle">
        {{ $t('strategy.subtitle') }}
      </p>
    </div>

    <div class="chat-container">
      <div class="messages-area" ref="messagesArea">
        <div v-if="messages.length === 0" class="welcome-message">
          <div class="welcome-card">
            <i class="fas fa-robot"></i>
            <h3>{{ $t('strategy.welcome.title') }}</h3>
            <p>{{ $t('strategy.welcome.description') }}</p>
            <div class="suggestion-cards">
              <div class="suggestion-card" @click="sendSuggestion('marketTrends')">
                <i class="fas fa-chart-trending-up"></i>
                <h4>{{ $t('strategy.welcome.marketTrends.title') }}</h4>
                <p>{{ $t('strategy.welcome.marketTrends.description') }}</p>
              </div>
              <div class="suggestion-card" @click="sendSuggestion('organizationalDevelopment')">
                <i class="fas fa-sitemap"></i>
                <h4>{{ $t('strategy.welcome.organizationalDevelopment.title') }}</h4>
                <p>{{ $t('strategy.welcome.organizationalDevelopment.description') }}</p>
              </div>
              <div class="suggestion-card" @click="sendSuggestion('capabilityExpansion')">
                <i class="fas fa-tools"></i>
                <h4>{{ $t('strategy.welcome.capabilityExpansion.title') }}</h4>
                <p>{{ $t('strategy.welcome.capabilityExpansion.description') }}</p>
              </div>
            </div>
          </div>
        </div>

        <div v-for="message in messages" :key="message.id" class="message" :class="message.sender">
          <div class="message-content">
            <div class="message-header">
              <i :class="message.sender === 'user' ? 'fas fa-user' : 'fas fa-robot'"></i>
              <span class="sender-name">{{ message.sender === 'user' ? $t('strategy.chat.you') : $t('strategy.chat.consultant') }}</span>
              <span class="timestamp">{{ formatTime(message.timestamp) }}</span>
            </div>
            <div class="message-text" v-html="formatMessage(message.content)"></div>
          </div>
        </div>

        <div v-if="isLoading" class="message ai">
          <div class="message-content">
            <div class="message-header">
              <i class="fas fa-robot"></i>
              <span class="sender-name">{{ $t('strategy.chat.consultant') }}</span>
            </div>
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>

      <div class="input-area">
        <div class="input-container">
          <textarea
            v-model="currentMessage"
            @keydown.enter.prevent="sendMessage"
            @keydown.shift.enter="currentMessage += '\n'"
            :placeholder="$t('strategy.chat.placeholder')"
            class="message-input"
            rows="1"
            :disabled="isLoading"
          ></textarea>
          <button 
            @click="sendMessage" 
            :disabled="!currentMessage.trim() || isLoading"
            class="send-button"
            :title="$t('strategy.chat.send')"
          >
            <i class="fas fa-paper-plane"></i>
          </button>
        </div>
        <div class="input-hint">
          {{ $t('strategy.chat.hint') }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

interface Message {
  id: string
  sender: 'user' | 'ai'
  content: string
  timestamp: Date
}

const { t } = useI18n()
const messages = ref<Message[]>([])
const currentMessage = ref('')
const isLoading = ref(false)
const messagesArea = ref<HTMLElement>()

const sendSuggestion = (type: string) => {
  let message = ''
  switch (type) {
    case 'marketTrends':
      message = t('strategy.welcome.marketTrends.description')
      break
    case 'organizationalDevelopment':
      message = t('strategy.welcome.organizationalDevelopment.description')
      break
    case 'capabilityExpansion':
      message = t('strategy.welcome.capabilityExpansion.description')
      break
  }
  currentMessage.value = message
  sendMessage()
}

const sendMessage = async () => {
  if (!currentMessage.value.trim() || isLoading.value) return

  const userMessage: Message = {
    id: Date.now().toString(),
    sender: 'user',
    content: currentMessage.value.trim(),
    timestamp: new Date()
  }

  messages.value.push(userMessage)
  const messageToSend = currentMessage.value.trim()
  currentMessage.value = ''
  isLoading.value = true

  await scrollToBottom()

  try {
    // 模擬 API 調用到商業顧問 Agent
    const response = await fetch('/api/conversation', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_prompt: `作為 Online Boutique 的商業顧問，請針對以下問題提供專業建議：${messageToSend}`,
        user_id: 'strategy-consultant',
        session_id: 'strategy-session'
      })
    })

    if (!response.ok) {
      throw new Error('網路請求失敗')
    }

    const data = await response.json()
    
    const aiMessage: Message = {
      id: (Date.now() + 1).toString(),
      sender: 'ai',
      content: data.agent_response || '抱歉，我現在無法提供建議，請稍後再試。',
      timestamp: new Date()
    }

    messages.value.push(aiMessage)
  } catch (error) {
    console.error('發送消息失敗:', error)
    const errorMessage: Message = {
      id: (Date.now() + 1).toString(),
      sender: 'ai',
      content: '抱歉，我現在無法回應您的問題。請檢查網路連接或稍後再試。',
      timestamp: new Date()
    }
    messages.value.push(errorMessage)
  } finally {
    isLoading.value = false
    await scrollToBottom()
  }
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesArea.value) {
    messagesArea.value.scrollTop = messagesArea.value.scrollHeight
  }
}

const formatTime = (date: Date) => {
  return date.toLocaleTimeString('zh-TW', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

const formatMessage = (content: string) => {
  // 簡單的 markdown 格式化
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
}

onMounted(() => {
  // 自動調整 textarea 高度
  const textarea = document.querySelector('.message-input') as HTMLTextAreaElement
  if (textarea) {
    textarea.addEventListener('input', () => {
      textarea.style.height = 'auto'
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
    })
  }
})
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as *;

.strategy-consultant {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.header {
  margin-bottom: $spacing-xl;
  text-align: center;

  .title {
    font-size: $font-2xl;
    font-weight: 700;
    color: $text-primary;
    margin-bottom: $spacing-md;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: $spacing-md;

    i {
      color: #f59e0b;
    }
  }

  .subtitle {
    color: $text-secondary;
    font-size: $font-lg;
    max-width: 600px;
    margin: 0 auto;
  }
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: $bg-primary;
  border-radius: 16px;
  border: 1px solid $bg-accent;
  overflow: hidden;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: $spacing-lg;
  max-height: 600px;
}

.welcome-message {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  min-height: 400px;
}

.welcome-card {
  text-align: center;
  max-width: 800px;

  i {
    font-size: 3rem;
    color: #3b82f6;
    margin-bottom: $spacing-lg;
  }

  h3 {
    font-size: $font-xl;
    font-weight: 600;
    color: $text-primary;
    margin-bottom: $spacing-md;
  }

  p {
    color: $text-secondary;
    margin-bottom: $spacing-xl;
  }
}

.suggestion-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: $spacing-md;
  margin-top: $spacing-xl;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    gap: $spacing-sm;
  }
  
  @media (min-width: 769px) and (max-width: 1024px) {
    grid-template-columns: repeat(2, 1fr);
  }
}

.suggestion-card {
  background: $bg-card;
  border: 1px solid $bg-accent;
  border-radius: 12px;
  padding: $spacing-lg;
  cursor: pointer;
  transition: all $transition-normal;

  &:hover {
    transform: translateY(-2px);
    box-shadow: $shadow-lg;
    border-color: #3b82f6;
  }

  i {
    font-size: $font-xl;
    color: #3b82f6;
    margin-bottom: $spacing-md;
  }

  h4 {
    font-size: $font-lg;
    font-weight: 600;
    color: $text-primary;
    margin-bottom: $spacing-sm;
  }

  p {
    color: $text-secondary;
    font-size: $font-sm;
    line-height: 1.5;
  }
}

.message {
  margin-bottom: $spacing-lg;
  display: flex;

  &.user {
    justify-content: flex-end;

    .message-content {
      background: linear-gradient(135deg, #3b82f6, #1d4ed8);
      color: white;
      max-width: 70%;
    }
  }

  &.ai {
    justify-content: flex-start;

    .message-content {
      background: $bg-card;
      border: 1px solid $bg-accent;
      max-width: 80%;
    }
  }
}

.message-content {
  border-radius: 16px;
  padding: $spacing-lg;
  box-shadow: $shadow-sm;
}

.message-header {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  margin-bottom: $spacing-sm;
  font-size: $font-sm;

  .sender-name {
    font-weight: 600;
  }

  .timestamp {
    opacity: 0.7;
    margin-left: auto;
  }
}

.message-text {
  line-height: 1.6;
  
  :deep(strong) {
    font-weight: 600;
  }
  
  :deep(em) {
    font-style: italic;
  }
}

.typing-indicator {
  display: flex;
  gap: 4px;
  align-items: center;
  
  span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: $text-secondary;
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
  border-top: 1px solid $bg-accent;
  padding: $spacing-lg;
  background: $bg-card;
}

.input-container {
  display: flex;
  gap: $spacing-md;
  align-items: flex-end;
}

.message-input {
  flex: 1;
  border: 1px solid $bg-accent;
  border-radius: 12px;
  padding: $spacing-md;
  font-size: $font-base;
  line-height: 1.5;
  resize: none;
  min-height: 44px;
  max-height: 120px;
  background: $bg-primary;
  color: $text-primary;
  transition: border-color $transition-normal;

  &:focus {
    outline: none;
    border-color: #3b82f6;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.send-button {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  color: white;
  border: none;
  border-radius: 12px;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all $transition-normal;

  &:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: $shadow-md;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
}

.input-hint {
  margin-top: $spacing-sm;
  font-size: $font-xs;
  color: $text-secondary;
  text-align: center;
}
</style>

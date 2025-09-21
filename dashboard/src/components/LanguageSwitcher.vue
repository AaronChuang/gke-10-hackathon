<template>
  <div class="language-switcher">
    <button 
      @click="toggleLanguage" 
      class="language-button"
      :title="$t('common.switchLanguage')"
    >
      <i class="fas fa-globe"></i>
      <span class="language-text">{{ currentLanguageLabel }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()

const currentLanguageLabel = computed(() => {
  return locale.value === 'en' ? 'EN' : '繁中'
})

const toggleLanguage = () => {
  locale.value = locale.value === 'en' ? 'zh-TW' : 'en'
  // 儲存到 localStorage
  localStorage.setItem('preferred-language', locale.value)
}

// 初始化時從 localStorage 讀取語言設定
const savedLanguage = localStorage.getItem('preferred-language')
if (savedLanguage && (savedLanguage === 'en' || savedLanguage === 'zh-TW')) {
  locale.value = savedLanguage
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as *;

.language-switcher {
  display: flex;
  align-items: center;
}

.language-button {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  background: $bg-card;
  border: 1px solid $bg-accent;
  border-radius: 8px;
  padding: $spacing-sm $spacing-md;
  cursor: pointer;
  transition: all $transition-normal;
  color: $text-secondary;
  font-size: $font-sm;
  font-weight: 500;

  &:hover {
    background: $bg-hover;
    border-color: #3b82f6;
    color: $text-primary;
    transform: translateY(-1px);
    box-shadow: $shadow-sm;
  }

  i {
    font-size: $font-base;
    color: #3b82f6;
  }

  .language-text {
    min-width: 32px;
    text-align: center;
  }
}
</style>

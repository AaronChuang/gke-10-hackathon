<template>
  <div class="error-container">
    <div class="error-icon">⚠️</div>
    <div class="error-content">
      <h3 class="error-title">連線錯誤</h3>
      <p class="error-message">{{ message }}</p>
      <button v-if="showRetry" @click="$emit('retry')" class="retry-button">
        重新連線
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  message: string
  showRetry?: boolean
}

withDefaults(defineProps<Props>(), {
  showRetry: true
})

defineEmits<{
  retry: []
}>()
</script>

<style lang="scss" scoped>
@use "sass:color";
.error-container {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  padding: $spacing-xl;
  background-color: rgba($status-failed, 0.1);
  border: 1px solid rgba($status-failed, 0.3);
  border-radius: $radius-lg;
  margin: $spacing-lg 0;
}

.error-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.error-content {
  flex: 1;
}

.error-title {
  color: $status-failed;
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: $spacing-xs;
}

.error-message {
  color: $text-secondary;
  font-size: 0.875rem;
  margin-bottom: $spacing-md;
}

.retry-button {
  background-color: $status-failed;
  color: $text-primary;
  border: none;
  padding: $spacing-xs $spacing-md;
  border-radius: $radius-md;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color $transition-normal;
  
  &:hover {
    background-color: color.adjust($status-failed, $lightness: -10%);
  }
  
  &:focus {
    outline: none;
    box-shadow: 0 0 0 2px rgba($status-failed, 0.5);
  }
}
</style>

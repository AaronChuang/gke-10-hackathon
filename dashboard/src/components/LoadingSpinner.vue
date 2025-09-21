<template>
  <div class="loading-container">
    <svg 
      class="loading-spinner animate-spin" 
      xmlns="http://www.w3.org/2000/svg" 
      fill="none" 
      viewBox="0 0 24 24"
    >
      <circle 
        class="opacity-25" 
        cx="12" 
        cy="12" 
        r="10" 
        stroke="currentColor" 
        stroke-width="4"
      />
      <path 
        class="opacity-75" 
        fill="currentColor" 
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
    <div class="loading-text">{{ message || $t('common.loading') }}</div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  message?: string
}

withDefaults(defineProps<Props>(), {
  message: '正在載入...'
})
</script>

<style lang="scss" scoped>
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: $spacing-2xl 0;
  text-align: center;
}

.loading-spinner {
  width: 2rem;
  height: 2rem;
  color: $status-running;
  margin-bottom: $spacing-md;
}

.loading-text {
  color: $text-muted;
  font-size: 0.875rem;
}
</style>

<script setup lang="ts">
defineProps({
  message: { type: String, default: '' },
  title: { type: String, default: 'Warnung' },
})
</script>

<template>
  <UAlert
      color="orange"
      icon="i-heroicons-exclamation-triangle"
      variant="subtle"
      :title="title"
      :description="message"
  />
</template>

<style scoped>

</style>

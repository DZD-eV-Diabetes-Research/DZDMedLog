<script setup lang="ts">
defineProps<{
  codeSystem: string;
  codeValue: string;
}>()
</script>

<template>
  <UBadge variant="outline" color="black" class="bg-white">
    <template #leading>
      <strong>{{ codeSystem }}</strong>
    </template>
    <template #default>
      <span class="font-mono">{{ codeValue }}</span>
    </template>
  </UBadge>
</template>

<style scoped>

</style>

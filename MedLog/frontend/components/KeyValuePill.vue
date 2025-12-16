<script setup lang="ts">
defineProps<{
  icon?: string;
  keyLabel: string;
  valueLabel: string;
}>()
</script>

<template>
  <UBadge variant="outline" color="black" class="bg-white items-baseline">
    <template #leading>
      <span v-if="icon">{{ icon }}</span>
      <strong>{{ keyLabel }}</strong>
    </template>
    <template #default>
      <span class="font-mono">{{ valueLabel }}</span>
    </template>
  </UBadge>
</template>

<style scoped>

</style>

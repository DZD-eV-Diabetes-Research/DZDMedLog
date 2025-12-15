<script setup lang="ts">
defineProps<{
  keyLabel: string;
  valueLabel: string;
}>()
</script>

<template>
  <UBadge variant="outline" color="black" class="bg-white items-baseline">
    <template #leading>
      <strong>{{ keyLabel }}</strong>
    </template>
    <template #default>
      <span class="font-mono">{{ valueLabel }}</span>
    </template>
  </UBadge>
</template>

<style scoped>

</style>

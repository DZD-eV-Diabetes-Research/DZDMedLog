<script setup lang="ts">
import type { SchemaSystemAnnouncement } from "#open-fetch-schemas/medlogapi";

const props = defineProps({
  announcement: {
    type: Object as () => SchemaSystemAnnouncement,
    required: true,
  }
});

const badge = computed(() => {
  switch (props.announcement.type) {
    case 'alert':
      return 'Kritisch'
    case 'warning':
      return 'Warnung'
    default:
      return 'Info'
  }
});

const color = computed(() => {
  switch (props.announcement.type) {
    case 'alert':
      return 'red'
    case 'warning':
      return 'amber'
    default:
      return 'sky'
  }
});

const icon = computed(() => {
  switch (props.announcement.type) {
    case 'alert':
      return 'i-heroicons-exclamation-circle-solid'
    case 'warning':
      return 'i-heroicons-exclamation-triangle-solid'
    default:
      return 'i-heroicons-information-circle-solid'
  }
});
</script>

<template>
  <UAlert :title="announcement.message" :color="color" :icon="icon" variant="subtle" :ui="{ inner: 'text-start' }">
    <template #icon>
      <UBadge :color="color" :icon="icon" :label="badge" />
    </template>
  </UAlert>
</template>

<style scoped>

</style>

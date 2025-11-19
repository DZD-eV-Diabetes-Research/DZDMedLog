<template>
  <UAlert color="red" :title="titleString" :ui="{ description: 'mt-1 text-sm leading-4 break-words' }">
    <template #description>
      <p>{{ messageString }}</p>
      <details v-if="detailsString" class="mt-3">
        <summary>Details</summary>
        <div class="bg-gray-200 text-black p-2 rounded">
          <code>
            {{ detailsString }}
          </code>
        </div>
      </details>
    </template>
  </UAlert>
</template>

<script setup lang="ts">
const props = defineProps<{
  error?: Error;
  title?: string
  message?: string
  details?: string
}>()

const titleString = computed(() => {
  if (props.title) {
    return props.title;
  }

  if (props.error) {
    return props.error.statusMessage ?? "Fehler";
  }

  return "";
});

const messageString = computed(() => {
  if (props.message) {
    return props.message;
  }

  if (props.error) {
    return props.error.message ?? props.error.toString() ?? "Unbekannter Fehler";
  }

  return "";
});

const detailsString = computed(() => {
  if (props.details) {
    return props.details;
  }

  if (props.error) {
    return props.error.data ?? "";
  }

  return "";
});
</script>

<style scoped>

</style>

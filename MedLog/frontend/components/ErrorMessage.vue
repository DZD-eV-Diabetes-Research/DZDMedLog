<template>
  <UAlert
      color="red"
      icon="i-heroicons-exclamation-circle"
      :title="titleString"
      :ui="{ description: 'mt-1 text-sm leading-4 break-words', title: 'font-semibold' }"
  >
    <template #description>
      <p>{{ messageString }}</p>
      <details v-if="detailsString && detailsString !== messageString" class="mt-3">
        <summary>Details</summary>
        <div class="bg-gray-200 text-black p-2 rounded">
          <code>
            {{ detailsString }}
          </code>
        </div>
      </details>
      <details v-if="causeString" class="mt-3">
        <summary>Ursache</summary>
        {{ causeString }}
      </details>
    </template>
  </UAlert>
</template>

<script setup lang="ts">
import { isFastAPIError } from "~/type-helper";

const props = defineProps<{
  error?: unknown;
  title?: string
  message?: string
  details?: string
}>()

const titleString = computed(() => {
  if (props.title) {
    return props.title;
  }

  if (props.error) {
    return isNuxtError(props.error) ? props.error.statusText : "Fehler";
  }

  return "";
});

const messageString = computed(() => {
  if (props.message) {
    return props.message;
  }

  if (props.error) {
    return useGetErrorMessage(props.error) ?? "Unbekannter Fehler";
  }

  return "";
});

const detailsString = computed(() => {
  if (props.details) {
    return props.details;
  }

  if (isNuxtError(props.error) && isFastAPIError(props.error.data)) {
    return props.error.data.detail;
  }

  if (props.error && isNuxtError(props.error)) {
    return props.error.data ?? "";
  }

  return "";
});

const causeString = computed(() => {
  if (props.error && typeof props.error === 'object' && 'cause' in props.error) {
    return String(props.error.cause);
  }

  return "";
})
</script>

<style scoped>

</style>

<script setup lang="ts">
const props = defineProps({
  value: {
    type: Boolean,
    required: false,
    default: undefined,
  },
  degraded: {
    type: Boolean,
    required: false,
    default: undefined,
  },
  okLabel: {
    type: String,
    default: "OK",
  },
  degradedLabel: {
    type: String,
    default: "Eingeschränkt",
  },
  failLabel: {
    type: String,
    default: "Fehler",
  },
});

const label = computed(() => {
  if (isUnknown.value) {
    return 'Unbekannt';
  }

  if (isFailed.value) {
    return props.failLabel;
  } else if (isDegraded.value) {
    return props.degradedLabel;
  }

  return props.okLabel;
});
const isDegraded = computed(() => {
  return props.degraded !== undefined && props.degraded;
});
const isFailed = computed(() => {
  return props.value !== undefined && !props.value;
});
const isUnknown = computed(() => {
  return props.value === undefined;
});
</script>

<template>
  <div class="inline-flex flex-row items-center">
    <span class="mr-0.5">{{ label }}</span>
    <UIcon v-if="isUnknown" name="i-heroicons-question-mark-circle-solid" class="text-gray-600 text-lg" />
    <UIcon v-else-if="isFailed" name="i-heroicons-x-circle-solid" class="text-red-600 text-lg" />
    <UIcon v-else-if="isDegraded" name="i-heroicons-exclamation-circle-solid" class="text-amber-600 text-lg" />
    <UIcon v-else name="i-heroicons-check-circle-solid" class="text-green-600 text-lg" />
  </div>
</template>

<style scoped>

</style>

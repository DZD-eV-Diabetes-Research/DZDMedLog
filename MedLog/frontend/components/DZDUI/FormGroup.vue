<script setup lang="ts">
defineProps({
  label: {
    type: String,
    default: '',
  },
  description: {
    type: String,
    default: '',
  },
});
</script>

<template>
  <UFormGroup :label="label">
    <template v-if="description" #label>
      <span class="inline-flex items-center gap-1">
        {{ label }}
        <UTooltip
            :text="description"
            :popper="{ placement: 'right' }"
            :ui="{ width: 'max-w-4xl' }"
        >
          <UIcon name="i-heroicons-question-mark-circle" class="w-4 h-4 cursor-pointer" />
        </UTooltip>
      </span>
    </template>

    <!-- Pass the default slot on to the UFormGroup so we can insert input elements from above -->
    <slot/>
  </UFormGroup>
</template>

<style scoped>

</style>

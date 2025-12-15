<script setup lang="ts">
defineProps({
  displayValue: { type: String, default: '' },
  fieldDefinition: { type: Object, required: true },
});
</script>

<template>
  <dt>
    {{ fieldDefinition.field_name_display }}
    <UTooltip v-if="fieldDefinition.field_desc" :text="fieldDefinition.field_desc" :popper="{ placement: 'right' }">
      <UIcon name="i-heroicons-question-mark-circle" class="w-4 h-4 text-black cursor-pointer" />
    </UTooltip>
  </dt>
  <dd>{{ displayValue ?? 'N/A' }}</dd>
</template>

<style scoped>
dt {
  grid-column-start: 1;
  background-color: lightyellow;
  padding: 0.2em 0.4em;
  font-weight: bold;
}

dt ~ dt, dd ~ dd {
  border-top: 2px solid darkgray;
}

dd {
  grid-column-start: 2;
  background-color: #fff;
  padding: 0.2em 0.4em;
}
</style>

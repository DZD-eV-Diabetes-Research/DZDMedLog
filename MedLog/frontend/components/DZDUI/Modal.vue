<script setup lang="ts">
interface Props {
  error?: unknown;
  title: string;
}

defineProps<Props>();

const modelValue = defineModel<boolean>();

function closeModal() {
  modelValue.value = false;
}
</script>

<template>
  <UModal v-model="modelValue" prevent-close>
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-lg">{{ title }}</span>
          <UButton color="gray" variant="ghost" icon="i-heroicons-x-mark-20-solid" class="-my-1" @click="closeModal" />
        </div>
      </template>

      <ErrorMessage v-if="error" :error="error" />

      <slot />
    </UCard>
  </UModal>
</template>

<style scoped>

</style>

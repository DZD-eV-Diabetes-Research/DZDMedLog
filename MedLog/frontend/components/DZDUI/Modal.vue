<script setup lang="ts">
interface Props {
  title: string;
  error?: unknown;
  ui?: Record<string, string>;
  showCloseButton?: boolean;
}

withDefaults(defineProps<Props>(), {
  error: undefined,
  ui: () => ({}),
  showCloseButton: true,
});

const modelValue = defineModel<boolean>();
const emit = defineEmits<{
  cancel: [];
  "after-leave": [];
}>();

function closeModal() {
  emit("cancel");
  modelValue.value = false;
}
</script>

<template>
  <UModal v-model="modelValue" :ui="ui" prevent-close @after-leave="emit('after-leave')">
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-lg">{{ title }}</span>
          <UButton
              v-if="showCloseButton"
              color="gray"
              variant="ghost"
              icon="i-heroicons-x-mark-20-solid"
              class="-my-1"
              @click="closeModal"
          />
        </div>
      </template>

      <ErrorMessage v-if="error" :error="error" />

      <slot />
    </UCard>
  </UModal>
</template>

<style scoped>

</style>

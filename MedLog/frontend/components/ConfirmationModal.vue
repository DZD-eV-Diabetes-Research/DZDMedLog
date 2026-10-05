<script setup lang="ts">
defineProps({
  title: { type: String, default: "Sind sie sicher?" },
  description: { type: String, default: "" },
  question: { type: String, default: "" },
  isDangerousToConfirm: { type: Boolean, default: false },
  cancelLabel: { type: String, default: "Abbrechen" },
  confirmLabel: { type: String, default: "Fortfahren" },
})

const modelValue = defineModel<boolean>();

defineEmits<{
  cancel: [];
  confirm: [];
}>()
</script>

<template>
  <DZDUIModal v-model="modelValue" :title="title" @cancel="$emit('cancel')">
    <slot name="description">
      <p v-if="description" class="break-words">
        {{ description }}
      </p>
    </slot>

    <slot name="question">
      <p v-if="question" class="break-words mt-2 font-semibold">
        {{ question }}
      </p>
    </slot>

    <div class="flex flex-row justify-between mt-4">
      <UButton
          :label="cancelLabel"
          color="gray"
          class="px-6"
          @click="$emit('cancel')"
      />
      <UButton
          :label="confirmLabel"
          :color="isDangerousToConfirm ? 'red' : 'green'"
          class="px-6"
          @click.once="$emit('confirm')"
      />
    </div>
  </DZDUIModal>
</template>

<style scoped>

</style>

<script setup lang="ts">
defineProps({
  title: { type: String, default: "Sind sie sicher?" },
  description: { type: String, default: "" },
  isDangerousToConfirm: { type: Boolean, default: false },
  cancelLabel: { type: String, default: "Abbrechen" },
  confirmLabel: { type: String, default: "Fortfahren" },
})

defineEmits(['cancel', 'confirm'])
</script>

<template>
  <UModal prevent-close>
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-lg">{{ title }}</span>
          <UButton color="gray" variant="ghost" icon="i-heroicons-x-mark-20-solid" class="-my-1" @click="$emit('cancel')" />
        </div>
      </template>

      <slot name="description">
        <p v-if="description" class="break-all">
          {{ description }}
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
            @click="$emit('confirm')"
        />
      </div>
    </UCard>
  </UModal>
</template>

<style scoped>

</style>

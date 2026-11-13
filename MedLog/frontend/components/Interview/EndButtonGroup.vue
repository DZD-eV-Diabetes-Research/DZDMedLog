<script setup lang="ts">
import CustomEndModal from "~/components/Interview/CustomEndModal.vue";

const modal = useModal();

interface Props {
  disabled?: boolean;
  endInterviewCallback: (date?: Date) => Promise<void>;
  startDate: Date;
}

withDefaults(defineProps<Props>(), {
  disabled: false,
});
</script>

<template>
  <UButtonGroup orientation="horizontal">
    <UButton
      label="Interview abschließen"
      color="red"
      icon="i-heroicons-stop-solid"
      title="Schließt das Interview mit der aktuellen Uhrzeit ab"
      :disabled="disabled"
      @click.once="endInterviewCallback()"
    />
    <UDropdown
      :items="[[
        {
          label: 'Interview nachträglich abschließen',
          slot: 'custom-interview-end',
          disabled: disabled,
          click: () => {
            modal.open(CustomEndModal, {
              startDate: startDate,
              submitCallback: async (data) => { await endInterviewCallback(data.interview_end_time_utc) }
            })
            },
        },
      ]]"
      :popper="{ placement: 'bottom-end' }"
      :ui="{ item: { base: 'flex-col' } }"
    >
      <UButton icon="i-heroicons-chevron-down-20-solid" color="red" :disabled="disabled" />

      <template #custom-interview-end>
        <span class="font-semibold text-left self-start">Interview nachträglich abschließen</span>
        <small class="text-left">Einen früheren Zeitpunkt als Ende des Interviews eintragen.</small>
      </template>
    </UDropdown>
  </UButtonGroup>
</template>

<style scoped>

</style>

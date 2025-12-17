<template>
  <UTable :rows="rows" :columns="columns" class="break-words">
    <template #pzn-data="{ row }">
      <div class="flex flex-col items-start gap-1">
        {{ row.pzn }}
        <UBadge
            v-if="row.intake.is_activeingredient_equivalent_choice"
            label="weicht ab"
            color="amber"
            variant="subtle"
            icon="i-heroicons-arrows-right-left"
        />
      </div>
    </template>

    <template #actions-data="{ row }">
      <UDropdown :items="myOptions(row)">
        <UButton color="gray" variant="ghost" icon="i-heroicons-ellipsis-horizontal-20-solid" />
      </UDropdown>
    </template>
  </UTable>
</template>

<script setup lang="ts">
const props = defineProps({
  intakes: { type: Array, required: true },
  showEvent: { type: Boolean, default: false },
  canEdit: { type: Boolean, default: false },
  canDelete: { type: Boolean, default: false },
})

const emit = defineEmits<{
  edit: [intakeId: string],
  delete: [row: object],
}>();

const columns: Array<{ key: string; label?: string, sortable?: boolean }> = [
  {
    key: "pzn",
    label: "Medikament PZN",
  },
  {
    key: "custom",
    label: "Custom",
    sortable: true,
  },
  {
    key: "name",
    label: "Medikament",
    sortable: true,
  },
  {
    key: "source",
    label: "Quelle der Angabe",
    sortable: true,
  },
  {
    key: "dose",
    label: "Dosis",
    sortable: true,
  },
  {
    key: "intervall",
    label: "Intervall",
    sortable: true,
  },
  {
    key: "time",
    label: "Einnahme Zeitraum",
    sortable: true,
  },
];

if (props.showEvent) {
  columns.unshift({
    key: 'event',
    label: 'Event',
    sortable: true
  })
}

if (props.canEdit || props.canDelete) {
  columns.push({
    key: "actions",
  });
}

function getIntakeDurationString(intake) {
  if (!intake.intake_start_time_utc && !intake.intake_end_time_utc) {
    return "unbekannt";
  }

  const startDate = intake.intake_start_time_utc === null ? 'unbekannt' : intake.intake_start_time_utc;
  const endDate = intake.intake_end_time_utc === null ? 'unbekannt' : intake.intake_end_time_utc;
  return `${startDate} bis ${endDate}`;
}

function myOptions(row) {
  const options = [];

  if (props.canEdit) {
    options.push({
      label: "Bearbeiten",
      icon: "i-heroicons-pencil-square-20-solid",
      click: () => emit('edit', row.intakeId),
    });
  }

  if (props.canDelete) {
    options.push({
      label: "Löschen",
      icon: "i-heroicons-trash-20-solid",
      click: () => emit('delete', row),
    });
  }

  return [options];
}

const rows = computed(() => {
  if (!props.intakes) {
    return [];
  }

  return props.intakes.map((item) => ({
    event: item.event.name,
    intake: item,
    pzn: item.drug.codes?.PZN,
    source: item.source_of_drug_information,
    name: item.drug.trade_name,
    dose: item.dose_per_day === 0 ? "-/-" : item.dose_per_day,
    intervall: useIntervallDoseTranslator(
        item.regular_intervall_of_daily_dose,
        null
    ),
    consumed_meds_today: item.consumed_meds_today,
    option: item.intake_regular_or_as_needed,
    startTime: item.intake_start_time_utc,
    endTime: item.intake_end_time_utc,
    time: getIntakeDurationString(item),
    intakeId: item.id,
    custom: item.drug?.is_custom_drug ? "Ja" : "Nein",
    class: item.drug?.is_custom_drug
        ? "bg-yellow-50"
        : null,
  }));
});
</script>

<style scoped>
/* I don't like that this is here but I can't get the wordbreak otherwise */
:deep(td) {
  white-space: normal !important;
  word-break: break-word !important;
}
</style>

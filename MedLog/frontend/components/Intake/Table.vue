<template>
  <UTable :rows="rows" :columns="columns" class="break-words">
    <template #event-data="{ row }">
      <UButton
          :to="`/studies/${row.intake.event.study_id}/proband/${row.intake.interview.proband_external_id}/interview/${row.intake.interview_id}`"
          :label="row.event"
          variant="link"
          icon="i-heroicons-arrow-right-circle"
          class="whitespace-nowrap"
          trailing
      />
    </template>

    <template #name-data="{ row }">
      <div class="flex flex-col items-start gap-1">
        <span class="font-semibold">
          {{ row.name }}
        </span>
        <UTooltip
          v-if="row.intake.drug.is_custom_drug"
          text="Dieses Medikament wurde manuell eingetragen"
          :popper="{ arrow: true, placement: 'right' }"
        >
          <UBadge label="Ungelistet" color="purple" size="xs" />
        </UTooltip>
        <UTooltip
            v-if="row.intake.is_activeingredient_equivalent_choice"
            text="Dieses Medikament wurde stellvertretend für Wirkstoff und Wirkstoffmenge gewählt."
            :popper="{ arrow: true, placement: 'right' }"
            :ui="{ width: 'max-w-lg' }"
        >
          <UBadge label="Alternative" color="amber" size="xs" />
        </UTooltip>
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
import type { SchemaIntakeDetailListItem } from "#open-fetch-schemas/medlogapi";
import type { ElementType, ValueOf } from "~/type-helper";
import {doseIntervalOptions, endDateOptions, startDateOptions} from "~/constants";
import useGetLabelForValue from "~/utils/useGetLabelForValue";

const toast = useToast();

const props = defineProps({
  intakes: { type: Array as () => SchemaIntakeDetailListItem[], required: true },
  showEvent: { type: Boolean, default: false },
  canEdit: { type: Boolean, default: false },
  canDelete: { type: Boolean, default: false },
})

const emit = defineEmits<{
  edit: [intakeId: string],
  delete: [row: ElementType<ValueOf<typeof rows>>],
}>();

const columns: Array<{ key: string; label?: string, sortable?: boolean }> = [
  {
    key: "pzn",
    label: "PZN",
  },
  {
    key: "name",
    label: "Medikament",
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

function getIntakeDurationString(intake: SchemaIntakeDetailListItem) {
  if (intake.intake_start_date && intake.intake_end_date) {
    return `${intake.intake_start_date} bis ${intake.intake_end_date}`;
  }

  const startDate = intake.intake_start_date === null ? useGetLabelForValue(startDateOptions, intake.intake_start_date_option) : intake.intake_start_date;
  const endDate = intake.intake_end_date === null ? useGetLabelForValue(endDateOptions, intake.intake_end_date_option) : intake.intake_end_date;
  return `Beginn: ${startDate}, Ende: ${endDate}`;
}

function myOptions(row: ElementType<ValueOf<typeof rows>>) {
  const options = [];

  if (!row.intakeId) {
    toast.add({
      title: "Kann Bearbeitung nicht starten",
      description: "intakeId ist leer",
    })
    return;
  }

  if (props.canEdit) {
    options.push({
      label: "Bearbeiten",
      icon: "i-heroicons-pencil-square-20-solid",
      click: () => emit('edit', row.intakeId as string), // cast should not be necessary as undefined is caught above
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
    pzn: item.is_activeingredient_equivalent_choice ? '' : item.drug.codes?.PZN,
    name: item.drug.trade_name,
    dose: item.dose_per_day === 0 ? "-/-" : item.dose_per_day,
    intervall: useGetLabelForValue(doseIntervalOptions, item.regular_intervall_of_daily_dose),
    time: getIntakeDurationString(item),
    intakeId: item.id,
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

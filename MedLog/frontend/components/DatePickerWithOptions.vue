<script setup lang="ts">
import type { SchemaIntakeDatePrecision } from "#open-fetch-schemas/medlogapi";
import { datePrecisionOptions, monthOptions } from "~/constants";

const selectedDate = defineModel('date', {
  type: String,
  required: false,
});
const selectedOptionValue = defineModel('option', {
  type: String,
  required: false,
});
const selectedPrecision = defineModel<SchemaIntakeDatePrecision | undefined>('precision', {
  required: false,
});

const props = defineProps<{
  options: Array<{ value: string; label: string; }>,
  earliestDate?: string,
}>();

const selectedOptionLabel = ref<string>('');
const selectedMonth = ref<string>();
const selectedYear = ref<string | number>(); // number input emits numbers

const earliestYear = computed(() => props.earliestDate?.slice(0, 4));
const currentYear = new Date().getFullYear();

const precisionRank: Record<SchemaIntakeDatePrecision, number> = { day: 0, month: 1, year: 2 };

function composeDateFromParts(precision?: SchemaIntakeDatePrecision): string | undefined {
  const year = String(selectedYear.value ?? '');
  if (!/^\d{4}$/.test(year)) {
    return undefined;
  }

  if (precision === 'year') {
    return `${year}-01-01`;
  }

  if (precision === 'month' && selectedMonth.value) {
    return `${year}-${selectedMonth.value}-01`;
  }

  return undefined;
}

function onPrecisionSelected(newPrecision: SchemaIntakeDatePrecision) {
  selectedOptionLabel.value = '';
  selectedOptionValue.value = undefined;

  const oldPrecision = selectedPrecision.value;
  selectedPrecision.value = newPrecision;

  if (!selectedDate.value || !oldPrecision || precisionRank[newPrecision] >= precisionRank[oldPrecision]) {
    // Same or coarser precision, keep the known parts and move the date to the start of the period
    if (newPrecision !== 'day') {
      selectedDate.value = composeDateFromParts(newPrecision);
    }
    return;
  }

  // Finer precision: the missing part has to be chosen explicitly, otherwise the start of the period would
  // silently become a placeholder day or month.
  if (newPrecision === 'month') {
    selectedMonth.value = undefined;
  }
  selectedDate.value = undefined;
}

function onOptionSelected(option: typeof props.options[number]): void {
  selectedOptionLabel.value = option.label;
  selectedOptionValue.value = option.value;
  selectedDate.value = undefined;
  selectedPrecision.value = undefined;
  selectedMonth.value = undefined;
  selectedYear.value = undefined;
}

const dropdownItems = computed(() => {
  const optionItems = props.options.map((item) => {
    return {
      label: item.label,
      click: () => {
        onOptionSelected(item);
      }
    };
  });

  const precisionItems = datePrecisionOptions.map((item) => {
    return {
      label: item.label,
      click: () => {
        onPrecisionSelected(item.value);
      }
    };
  });

  return [optionItems, precisionItems];
});

watch([selectedMonth, selectedYear], () => {
  if (selectedPrecision.value === 'month' || selectedPrecision.value === 'year') {
    selectedDate.value = composeDateFromParts(selectedPrecision.value);
  }
});

watch([selectedDate, selectedOptionValue, selectedPrecision], ([newSelectedDate, newSelectedOptionValue, newSelectedPrecision]) => {
  if (newSelectedDate) {
    // Dates without precision are exact days, as in the backend
    const precision = newSelectedPrecision ?? 'day';
    selectedPrecision.value = precision;
    selectedOptionLabel.value = '';
    selectedYear.value = newSelectedDate.slice(0, 4);
    selectedMonth.value = precision === 'year' ? undefined : newSelectedDate.slice(5, 7);
  } else if (newSelectedOptionValue) {
    selectedPrecision.value = undefined;
    const foundOption = props.options.find((option) => option.value === newSelectedOptionValue);
    if (foundOption) {
      selectedOptionLabel.value = foundOption.label;
    } else {
      // Probably invalid option value, reset choice
      selectedOptionValue.value = undefined;
      selectedOptionLabel.value = '';
    }
  }
});
</script>

<template>
  <UButtonGroup orientation="horizontal">
    <UBadge
        v-show="!selectedPrecision && !selectedOptionLabel"
        label="Bitte wählen"
        color="white"
    />
    <UBadge
        v-show="!selectedPrecision && selectedOptionLabel"
        :label="selectedOptionLabel"
        color="white"
    />
    <UInput
        v-show="selectedPrecision === 'day'"
        v-model="selectedDate"
        type="date"
        :min="earliestDate"
    />
    <USelect
        v-show="selectedPrecision === 'month'"
        v-model="selectedMonth"
        :options="monthOptions"
        placeholder="Monat"
    />
    <UInput
        v-show="selectedPrecision === 'month' || selectedPrecision === 'year'"
        v-model="selectedYear"
        type="number"
        inputmode="numeric"
        placeholder="Jahr"
        :min="earliestYear"
        :max="currentYear"
        class="w-24"
    />
    <UDropdown
      :items="dropdownItems"
      :popper="{ placement: 'bottom-end' }"
    >
      <UButton icon="i-heroicons-chevron-down-20-solid" color="green" />
    </UDropdown>
  </UButtonGroup>
</template>

<style scoped>

</style>

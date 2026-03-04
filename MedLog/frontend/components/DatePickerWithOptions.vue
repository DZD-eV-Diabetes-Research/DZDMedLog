<script setup lang="ts">
const selectedDate = defineModel('date', {
  type: String,
  required: false,
});
const selectedOptionValue = defineModel('option', {
  type: String,
  required: false,
});

const props = defineProps<{
  options: Array<{ value: string; label: string; }>,
}>();

const dateSelectionMode = ref<boolean>(false);
const selectedOptionLabel = ref<string>('');

function onDateOptionSelected() {
  dateSelectionMode.value = true;
  selectedOptionLabel.value = '';
  selectedOptionValue.value = undefined;
}

function onOptionSelected(option: typeof props.options[number]): void {
  selectedOptionLabel.value = option.label;
  selectedOptionValue.value = option.value;
  selectedDate.value = undefined;
  dateSelectionMode.value = false;
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

  const fixedItems = [{
    label: 'Exaktes Datum wählen',
    click: () => { onDateOptionSelected() },
  }];

  return [optionItems, fixedItems];
});
</script>

<template>
  <UButtonGroup orientation="horizontal">
    <UBadge
        v-show="!dateSelectionMode && !selectedOptionLabel"
        label="Bitte wählen"
        color="white"
    />
    <UBadge
        v-show="!dateSelectionMode && selectedOptionLabel"
        :label="selectedOptionLabel"
        color="white"
    />
    <UInput
        v-show="dateSelectionMode"
        v-model="selectedDate"
        type="date"
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

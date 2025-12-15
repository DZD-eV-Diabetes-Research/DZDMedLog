<script setup lang="ts">
import type {SchemaDisplayPriorityClass} from "#open-fetch-schemas/medlogapi";

const drugFieldsStore = useDrugFields();

const props = defineProps({
  drug: { type: Object, required: true },
})

defineEmits(['drugSelected']);

const drugCodeSystems = drugFieldsStore.codes.filter((item) => item.client_visible === true)

const showDetails = ref(false);

const dataTableItems = computed(() => {
  const items = prioritizedFieldDefinitions.value[2] ?? [];
  if (showDetails.value) {
    return items.concat(prioritizedFieldDefinitions.value[3] ?? [])
  }
  return items;
});

const keyValuePills = computed(() =>  {
  const pills = [];

  if (Object.hasOwn(props.drug, 'codes')) {
    for (const drugCodeSystem of drugCodeSystems) {
      if (Object.hasOwn(props.drug.codes, drugCodeSystem.id)) {
        pills.push({
          label: drugCodeSystem.id,
          value: props.drug.codes?.[drugCodeSystem.id]
        });
      }
    }
  }

  if (prioritizedFieldDefinitions.value[1] ?? []) {
    for (const { fieldDefinition, attributeClass } of prioritizedFieldDefinitions.value[1]) {
      pills.push({ label: fieldDefinition.field_name_display, value: getDisplayValue(fieldDefinition, attributeClass) });
    }
  }

  // Only include entries with a value
  return pills.filter(item => item.value);
});

const prioritizedFieldDefinitions = computed(() => {
  const fields: Record<SchemaDisplayPriorityClass, { attributeClass: string, fieldDefinition: any }[]> = { 1: [], 2: [], 3: [] };
  for (const attributeClass of Object.keys(drugFieldsStore.fieldsForSearchResults)) {
    for (const fieldDefinition of drugFieldsStore.fieldsForSearchResults[attributeClass]) {
      fields[fieldDefinition.field_display_priority_class].push({ attributeClass, fieldDefinition });
    }
  }
  return fields;
});

function getDisplayValue(attribute, attributeClass): string {
  const value = props.drug?.[attributeClass]?.[attribute.field_name];

  if (attribute.is_multi_val_field && attribute.is_reference_list_field) {
    return value?.map(item => item.display).join(', ');
  } else if (attribute.is_multi_val_field && !attribute.is_reference_list_field) {
    return value?.join(', ');
  } else if (!attribute.is_multi_val_field && attribute.is_reference_list_field) {
    return value?.display;
  }

  return String(value);
}

</script>

<template>
  <li
      class="border border-blue-400 my-1 p-2 rounded-md bg-blue-100 hover:bg-blue-200 flex flex-col"
  >
    <div class="flex flex-row justify-between gap-2">
      <div>
        <strong>{{ drug.trade_name }}</strong><br>
        <div v-if="keyValuePills" class="flex flex-row flex-wrap">
          <KeyValuePill
              v-for="{ label, value } in keyValuePills"
              :key="label"
              :key-label="label"
              :value-label="value"
              class="mr-2 mb-1"
          />
        </div>
      </div>
      <div>
        <UButtonGroup orientation="horizontal">
          <UButton
              label="Übernehmen"
              @click="$emit('drugSelected', false)"
          />
          <UDropdown
              :items="[[
            {
              label: 'Als Wirkstoff-äquivalent übernehmen',
              slot: 'activeIngredientOnly',
              click: () => {
                $emit('drugSelected', true)
              }
            },
          ]]"
              :popper="{ placement: 'bottom-end' }"
              :ui="{ item: { base: 'flex-col' } }"
          >
            <UButton icon="i-heroicons-chevron-down-20-solid" color="green" />

            <template #activeIngredientOnly>
              <span class="font-semibold text-left">Als Wirkstoff-äquivalent übernehmen</span>
              <small class="text-left">Dieses Präparat stellvertretend für Wirkstoff und Wirkstoffmenge auswählen. Das exakte Produkt ist unbekannt.</small>
            </template>
          </UDropdown>
        </UButtonGroup>
      </div>
    </div>

    <div v-if="dataTableItems.length" class="flex flex-row gap-2 items-end">
      <dl class="grow">
        <DrugDataTableItem
            v-for="{ fieldDefinition, attributeClass } in dataTableItems"
            :key="fieldDefinition.field_name"
            :field-definition="fieldDefinition"
            :display-value="getDisplayValue(fieldDefinition, attributeClass)"
        />
      </dl>

      <UButton
          :disabled="(prioritizedFieldDefinitions[3] ?? []).length == 0"
          :title="showDetails ? 'Details verstecken' : 'Details zeigen'"
          variant="outline"
          :icon="showDetails ? 'heroicons-chevron-up' : 'i-heroicons-information-circle'"
          class="mt-2 bg-white"
          @click="showDetails = !showDetails"
      />
    </div>
  </li>
</template>

<style scoped>
dl {
  display: grid;
  grid-template-columns: max-content auto;
  margin-top: 0.75em;
  box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19);
  border-radius: 1rem;
  overflow: hidden;
  background-color: #fff;
}
</style>

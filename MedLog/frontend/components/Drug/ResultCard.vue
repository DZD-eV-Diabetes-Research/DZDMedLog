<script setup lang="ts">
import { computed, ref } from "#imports";
import type {
  SchemaDisplayPriorityClass,
  SchemaDrugAttrFieldDefinitionContainer,
  SchemaDrugCodeSystem,
  SchemaMedLogSearchEngineResult,
} from "#open-fetch-schemas/medlogapi";
import {type FieldDefinition, isMultiRefField, isMultiValueField, isSingleRefField} from "~/type-helper";

const drugFieldsStore = useDrugFields();

const props = defineProps({
  drug: { type: Object as () => SchemaMedLogSearchEngineResult["drug"], required: true },
})

defineEmits<{
  drugSelected: [activeIngredientOnly: boolean],
}>();

const drugCodeSystems = drugFieldsStore.clientVisibleCodes
    .sort((a: SchemaDrugCodeSystem, b: SchemaDrugCodeSystem) => {
      if (a.code_display_sort_order == b.code_display_sort_order) {
        return 0;
      }

      if (a.code_display_sort_order === null) {
        return 1;
      } else if (b.code_display_sort_order === null) {
        return -1;
      }

      return a.code_display_sort_order - b.code_display_sort_order;
    })

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

  if ('codes' in props.drug && typeof props.drug.codes === 'object') {
    for (const drugCodeSystem of drugCodeSystems) {
      if (Object.hasOwn(props.drug.codes, drugCodeSystem.id)) {
        pills.push({
          icon: drugCodeSystem.code_icon ?? undefined,
          label: drugCodeSystem.id,
          value: props.drug.codes[drugCodeSystem.id as keyof typeof props.drug.codes] ?? ""
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
  const fields: Record<SchemaDisplayPriorityClass, { attributeClass: keyof SchemaDrugAttrFieldDefinitionContainer, fieldDefinition: FieldDefinition }[]> = { 1: [], 2: [], 3: [] };

  // Group field definitions by priority class
  for (const attributeClassString of Object.keys(drugFieldsStore.fieldsForSearchResults)) {
    const attributeClass = attributeClassString as keyof typeof drugFieldsStore.fieldsForSearchResults;
    for (const fieldDefinition of drugFieldsStore.fieldsForSearchResults[attributeClass] as FieldDefinition[]) {
      if (fieldDefinition.field_display_priority_class && Object.keys(fields).includes(String(fieldDefinition.field_display_priority_class))) {
        fields[fieldDefinition.field_display_priority_class].push({ attributeClass, fieldDefinition });
      }
    }
  }

  // Sort within priority classes
  for (const priorityClassArray of Object.values(fields)) {
    priorityClassArray.sort((a, b) => {
      if (a.fieldDefinition.field_display_sort_order == b.fieldDefinition.field_display_sort_order) {
        return 0;
      }

      if (a.fieldDefinition.field_display_sort_order === null) {
        return 1;
      } else if (b.fieldDefinition.field_display_sort_order === null) {
        return -1;
      }

      return a.fieldDefinition.field_display_sort_order - b.fieldDefinition.field_display_sort_order;
    });
  }

  return fields;
});

function getDisplayValue(fieldDefinition: FieldDefinition, attributeClass: keyof SchemaDrugAttrFieldDefinitionContainer): string {
  const fields = props.drug[attributeClass];

  if (!fields || !fieldDefinition.field_name || !(fieldDefinition.field_name in fields)) {
    return "ERROR";
  }

  // Seems repetitive, but ensures type safety
  if (isMultiRefField(fieldDefinition, fields)) {
    const field = fields[fieldDefinition.field_name as keyof typeof fields];
    return field ? field.map(item => item.display).join(', ') : "";
  } else if (isMultiValueField(fieldDefinition, fields)) {
    const field = fields[fieldDefinition.field_name as keyof typeof fields];
    return field.join(', ');
  } else if (isSingleRefField(fieldDefinition, fields)) {
    const field = fields[fieldDefinition.field_name as keyof typeof fields];
    return field ? field.display ?? "" : "";
  }

  const field = fields[fieldDefinition.field_name as keyof typeof fields];
  return String(field ?? "");
}

</script>

<template>
  <li
      class="border border-blue-400 my-2 p-2 rounded-md bg-blue-100 hover:bg-blue-200 flex flex-col"
  >
    <div class="flex flex-row justify-between gap-2">
      <div>
        <strong>{{ drug.trade_name }}</strong><br>
        <div v-if="keyValuePills" class="flex flex-row flex-wrap">
          <KeyValuePill
              v-for="{ label, value, icon } in keyValuePills"
              :key="label"
              :icon="icon"
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
      <dl class="grow text-sm">
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
  box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.2), 0 3px 10px 0 rgba(0, 0, 0, 0.1);
  border-radius: 1rem;
  overflow: hidden;
  background-color: #fff;
}
</style>

<script setup lang="ts">
import { computed, ref } from "#imports";
import type {
  SchemaDrugAttrFieldDefinitionContainer,
  SchemaDrugCodeSystem,
  SchemaMedLogSearchEngineResult,
} from "#open-fetch-schemas/medlogapi";
import {type FieldDefinition, isMultiRefField, isMultiValueField, isSingleRefField} from "~/type-helper";
import { useDayjs } from '#dayjs'
import localizedFormat from 'dayjs/plugin/localizedFormat'

const dayjs = useDayjs();
const drugFieldsStore = useDrugFields();

dayjs.extend(localizedFormat);

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
  return useGetPrioritizedFieldDefinitions(drugFieldsStore.fieldsForSearchResults);
});

const accessDate = computed(() => Date.parse(props.drug.market_access_date ?? ""));
const exitDate = computed(() => Date.parse(props.drug.market_exit_date ?? ""));
const now = computed(() => Date.now() );

const isCurrentlySold = computed(() => {
  if (Number.isNaN(accessDate.value) && Number.isNaN(exitDate.value)) {
    return true;
  }

  return !(exitDate.value < now.value || accessDate.value > now.value);
});

const marketStatusText = computed((): string => {
  if (accessDate.value > now.value) {
    return `Erst ab ${dayjs.utc(accessDate.value).local().format('LL')} im Verkauf`;
  } else if (exitDate.value < now.value) {
    return `Seit ${dayjs.utc(exitDate.value).local().format('LL')} nicht mehr im Verkauf`;
  }

  return ""
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
      class="border my-2 p-2 rounded-md flex flex-col"
      :class="{
          'border-blue-400': isCurrentlySold && !drug.is_custom_drug,
          'bg-blue-100': isCurrentlySold && !drug.is_custom_drug,
          'hover:bg-blue-200': isCurrentlySold && !drug.is_custom_drug,
          'border-gray-400': !isCurrentlySold && !drug.is_custom_drug,
          'bg-gray-100': !isCurrentlySold && !drug.is_custom_drug,
          'hover:bg-gray-200': !isCurrentlySold && !drug.is_custom_drug,
          'border-purple-400': drug.is_custom_drug,
          'bg-purple-100': drug.is_custom_drug,
          'hover:bg-purple-200': drug.is_custom_drug,
      }"
  >
    <div class="flex flex-row justify-between gap-2">
      <div>
        <strong>{{ drug.trade_name }}</strong>
        <UTooltip v-if="drug.is_custom_drug" text="Dieses Medikament wurde manuell eingetragen" :popper="{ arrow: true, placement: 'right' }">
          <UBadge label="Ungelistet" color="purple" size="xs" class="ml-2"/>
        </UTooltip>
        <UTooltip v-if="!isCurrentlySold" :text="marketStatusText" :popper="{ arrow: true, placement: 'right' }">
          <UBadge icon="i-heroicons-shopping-cart" label="Nicht im Verkauf" color="gray" size="xs" class="ml-2"/>
        </UTooltip>
        <br>
        <div v-if="keyValuePills" class="flex flex-row flex-wrap mt-1">
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

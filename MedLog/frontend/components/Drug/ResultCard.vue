<script setup lang="ts">
const props = defineProps({
  drug: { type: Object, required: true },
})

defineEmits(['drugSelected']);

const showDetails = ref(false);

const drugFieldsStore = useDrugFields();

const drugCodeSystems = drugFieldsStore.codes.filter((item) => item.client_visible === true)

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

  // Only include entries with a value
  return pills.filter(item => item.value);
});

function getDisplayValue(attribute, attributeClass) {
  const value = props.drug?.[attributeClass]?.[attribute.field_name];

  if (attribute.is_multi_val_field && attribute.is_reference_list_field) {
    return value?.map(item => item.display).join(', ');
  } else if (attribute.is_multi_val_field && !attribute.is_reference_list_field) {
    return value?.join(', ');
  } else if (!attribute.is_multi_val_field && attribute.is_reference_list_field) {
    return value?.display;
  }

  return value;
}

</script>

<template>
  <li
      class="border border-blue-400 my-1 p-2 rounded-md bg-blue-100 hover:bg-blue-200 flex flex-col"
  >
    <div class="flex flex-row justify-between gap-2">
      <div>
        <strong>{{ drug.trade_name }}</strong><br>
        <div v-if="keyValuePills" class="flex flex-row">
          <DrugCodePill
              v-for="{ label, value } in keyValuePills"
              :key="label"
              :code-system="label"
              :code-value="value"
              class="mr-2"
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

    <div class="flex flex-row justify-between gap-2 items-end">
      <dl v-if="showDetails">
        <template v-for="attributeClass in Object.keys(drugFieldsStore.fieldsForSearchResults)">
          <template v-for="attribute in drugFieldsStore.fieldsForSearchResults[attributeClass]" :key="attribute.field_name">
            <dt>
              {{ attribute.field_name_display }}
              <UTooltip v-if="attribute.field_desc" :text="attribute.field_desc" :popper="{ placement: 'right' }">
                <UIcon name="i-heroicons-question-mark-circle" class="w-4 h-4 text-black cursor-pointer" />
              </UTooltip>
            </dt>
            <dd>{{ getDisplayValue(attribute, attributeClass) ?? 'N/A' }}</dd>
          </template>
        </template>
      </dl>
      <div v-else>
        <!-- Placeholder to keep the button on the right -->
        &nbsp;
      </div>

      <UButton
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

dt {
  grid-column-start: 1;
  background-color: lightyellow;
  padding: 0.2em 0.4em;
  font-weight: bold;
}

dt ~ dt, dd ~ dd {
  border-top: 2px solid darkgray;
}

dd {
  grid-column-start: 2;
  background-color: #fff;
  padding: 0.2em 0.4em;
}
</style>

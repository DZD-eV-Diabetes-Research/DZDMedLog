<script setup lang="ts">
const props = defineProps({
  drug: { type: Object, required: true },
})

defineEmits(['drugSelected']);

const showDetails = ref(false);

const drugFieldsStore = useDrugFields();

const drugCodeSystems = drugFieldsStore.codes.filter((item) => item.client_visible === true)

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
      class="border border-blue-400 my-1 p-2 rounded-md bg-blue-100 hover:bg-blue-200 flex flex-row justify-between"
  >
    <div>
      <strong>{{ drug.trade_name }}</strong><br>
      <DrugCodePill
          v-for="drugCodeSystem in drugCodeSystems"
          :key="drugCodeSystem.id"
          :code-system="drugCodeSystem.id"
          :code-value="drug.codes?.[drugCodeSystem.id]"
          class="mr-2"
      />
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
    </div>
    <div class="flex flex-col justify-between ml-3">
      <UButton icon="i-heroicons-arrow-right-circle" @click="$emit('drugSelected')" />
      <UButton
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

<script setup lang="ts">
import type { FieldDefinition } from "~/type-helper";

const { $medlogapi } = useNuxtApp();
const toast = useToast();

interface Option {
  value: string | number | boolean;
  display: string;
}

const model = defineModel<Option['value'] | Option['value'][]>();

const props = defineProps({
  fieldDefinition: {
    type: Object as () => FieldDefinition,
    required: true,
  },
  multiple: {
    type: Boolean,
    default: false,
  },
  required: {
    type: Boolean,
    default: false,
  },
});

const cachedOptions = ref<Option[]>([]);
const loading = ref<boolean>(false);
const searchable = ref<boolean | ((query: string) => Promise<Option[]>)>(onSearch);

const multiValueLabel = computed((): string => {
  if (!(model.value && Array.isArray(model.value) && model.value.length > 0)) {
    return "";
  }

  return cachedOptions.value.filter(option => (model.value as Option['value'][]).includes(option.value)).map(option => option.display).join('; ');
});

async function onSearch(query: string): Promise<Option[]> {
  console.log('onSearch', query);
  // An empty search is performed on initialization of the component
  if (query === '') {
    return cachedOptions.value;
  }

  try {
    loading.value = true;
    const response = await $medlogapi("/api/drug/field_def/{field_name}/refs", {
      path: {
        field_name: props.fieldDefinition.field_name,
      },
      query: {
        search_term: query,
      }
    });

    // Cache search results, the component does not remember on its own
    // Otherwise, the multiValueLabel would not show all the selected values
    for (const item of response.items) {
      if (cachedOptions.value.find(cachedOption => cachedOption.value == item.value)) {
        continue;
      }

      cachedOptions.value.push({
        value: item.value,
        display: item.display,
      })
    }

    return response.items.map(item => {
      return {
        value: item.value,
        display: item.display,
      };
    })
  } catch (error) {
    toast.add({
      title: "Fehler bei der Suche",
      description: useGetErrorMessage(error),
    });
    return cachedOptions.value;
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  if (!props.multiple && !props.required) {
    // Add empty option for optional single selection
    cachedOptions.value.push({ value: '', display: 'Keine Auswahl'});
  }

  // Initialize options with the first page of results
  const response = await $medlogapi("/api/drug/field_def/{field_name}/refs", {
    path: {
      field_name: props.fieldDefinition.field_name,
    },
  });
  for (const item of response.items) {
    cachedOptions.value.push({
      value: item.value,
      display: item.display,
    })
  }

  /*
   No search necessary if we received all the results
   Making false the default and setting the search function here if necessary did not work
  */
  if (!response.total_count || response.count >= response.total_count) {
    searchable.value = false;
  }
});
</script>

<template>
  <USelectMenu
      v-model="model"
      :options="cachedOptions"
      value-attribute="value"
      option-attribute="display"
      :debounce="500"
      :loading="loading"
      :multiple="multiple"
      :placeholder="multiple ? 'Mehrfachauswahl möglich' : 'Option auswählen'"
      :required="required"
      :searchable="searchable"
  >
    <template v-if="multiple && multiValueLabel" #label>
      {{ multiValueLabel }}
    </template>
  </USelectMenu>
</template>

<style scoped>

</style>

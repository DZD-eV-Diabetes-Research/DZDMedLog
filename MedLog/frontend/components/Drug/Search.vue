<template>
  <div>
    <UFormGroup name="drug" class="mb-4">
      <UInput
          v-model="searchTerm"
          :autofocus="autofocusInput"
          placeholder="Medikament/PZN oder ATC-Code eingeben"
          icon="i-heroicons-magnifying-glass-20-solid"
          :ui="{ icon: { trailing: { pointer: '' } } }"
      >
        <template #trailing>
          <UButton
              v-show="searchTerm !== ''"
              color="gray"
              variant="link"
              icon="i-heroicons-x-mark-20-solid"
              :padded="false"
              @click="searchTerm = ''"
          />
        </template>
      </UInput>
    </UFormGroup>

    <div class="h-6 flex flex-col">
      <UProgress v-if="isLoading" animation="carousel" />
      <p v-else class="text-sm self-end">{{ resultsText }}</p>
    </div>

    <ErrorMessage v-if="searchError" title="Fehler bei der Medikamentensuche" :error="searchError" />

    <UAlert v-else-if="warningMessage" color="amber" variant="subtle" :title="warningMessage" />

    <div v-if="searchResults.length > 0" class="flex flex-col gap-2">

      <UPagination
          v-if="searchResults.length > itemsPerPage"
          v-model="currentPage"
          :page-count="itemsPerPage"
          :total="searchResults.length"
          class="self-center"
      />
      <div :style="searchResults.length > itemsPerPage ? 'min-height: 30rem;' : ''">
        <ul>
          <DrugResultCard
              v-for="item in paginatedItems"
              :key="item.drug.id"
              :drug="item.drug"
              @drug-selected="(activeIngredientOnly: boolean) => selectDrug(item, activeIngredientOnly)"
          />
        </ul>
      </div>
      <UPagination
          v-if="searchResults.length > 5"
          v-model="currentPage"
          :page-count="itemsPerPage"
          :total="searchResults.length"
          class="self-center"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "#imports";
import type {SchemaMedLogSearchEngineResult} from "#open-fetch-schemas/medlogapi";

const itemsPerPage = 5;
const searchItemLimit = 100;

defineProps({
  autofocusInput: { type: Boolean, default: false },
});

const emit = defineEmits(['drug-selected'])

const currentPage = ref(1);
const isLoading = ref(false);
const searchError = ref();
const searchResults = ref<SchemaMedLogSearchEngineResult[]>([]);
const searchTerm = ref("");
const totalCount = ref(0);
const warningMessage = ref("");

const fetchDrugs = async (searchTerm: string) => {
  searchError.value = undefined;
  warningMessage.value = "";

  if (searchTerm === "") {
    searchResults.value = [];
    return;
  } else if (searchTerm.length < 3) {
    searchResults.value = [];
    warningMessage.value = "Für die Suche sind mindestens 3 Zeichen erforderlich";
    return;
  }

  isLoading.value = true;
  try {
    const response = await useGetDrugSearch(searchTerm, searchItemLimit)

    if (response?.total_count === 0) {
      warningMessage.value = "Die Suche ergab keine Treffer."
    }

    searchResults.value = response?.items ?? [];
    totalCount.value = response?.total_count ?? 0;
    currentPage.value = 1;
  } catch (error) {
    searchError.value = error;
    searchResults.value = [];
  } finally {
    isLoading.value = false;
  }
};

let debounceTimeout: NodeJS.Timeout | undefined = undefined;

watch(
  () => searchTerm.value,
  (newValue) => {
    if (debounceTimeout !== undefined) {
      clearTimeout(debounceTimeout);
      debounceTimeout = undefined;
    }

    // Empty search is executed immediately
    if (newValue === "") {
      fetchDrugs(newValue);
      return;
    }

    // Otherwise wait a bit for more input, so we are not sending a query for every keystroke
    debounceTimeout = setTimeout(fetchDrugs, 500, newValue);
  },
  { immediate: false }
);

const resultsText = computed(() => {
  if (totalCount.value > searchItemLimit) {
    return `Zeige ${ searchResults.value.length } Ergebnisse von insgesamt ${ totalCount.value }`;
  } else {
    return `${ searchResults.value.length } ${ searchResults.value.length == 1 ? 'Ergebnis' : 'Ergebnisse' }`;
  }
});

const paginatedItems = computed(() => {
  const startIndex = (currentPage.value - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  return searchResults.value.slice(startIndex, endIndex);
});

function selectDrug(item: SchemaMedLogSearchEngineResult, activeIngredientOnly: boolean) {
  searchTerm.value = "";
  emit('drug-selected', item.drug_id, activeIngredientOnly);
}
</script>

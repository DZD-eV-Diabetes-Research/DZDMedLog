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
              @drug-selected="selectDrug(item)"
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
import { ref, watch } from "vue";
import { apiDrugSearch } from '~/api/drug';

const itemsPerPage = 5;
const searchItemLimit = 100;

defineProps({
  autofocusInput: { type: Boolean, default: false },
});

const emit = defineEmits(['drug-selected'])

const currentPage = ref(1);
const isLoading = ref(false);
const searchError = ref();
const searchResults = ref([]);
const searchTerm = ref("");
const totalCount = ref(0);
const warningMessage = ref("");

const fetchDrugs = async (searchTerm) => {
  searchError.value = undefined;
  isLoading.value = true;
  try {
    warningMessage.value = ''
    const response = await apiDrugSearch(searchTerm, searchItemLimit)

    if (response.total_count === 0) {
      warningMessage.value = `Kein Medikament zur Eingabe "${searchTerm}" gefunden`
    }

    searchResults.value = response.items ?? [];
    totalCount.value = response.total_count;
    currentPage.value = 1;
  } catch (error) {
    searchError.value = error;
    searchResults.value = [];
  } finally {
    isLoading.value = false;
  }
};

watch(
  () => searchTerm.value,
  (newValue) => {
    if (newValue && newValue.length >= 3) {
      fetchDrugs(newValue);
    } else if (newValue === "") {
      searchError.value = undefined;
      warningMessage.value = "";
    }
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

function selectDrug(item) {
  searchTerm.value = "";
  emit('drug-selected', item.drug_id);
}
</script>

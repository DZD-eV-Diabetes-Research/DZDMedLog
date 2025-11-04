<template>
  <div>
    <UFormGroup name="drug" class="mb-4">
      <UInput
          v-model="state.searchTerm"
          :autofocus="autofocusInput"
          placeholder="Medikament/PZN oder ATC-Code eingeben"
          icon="i-heroicons-magnifying-glass-20-solid"
      >
        <template #trailing>
          <UIcon
              v-show="isLoading"
              name="i-heroicons-x-mark-20-solid"
          />
        </template>
      </UInput>
    </UFormGroup>

    <UAlert v-if="errorMessage" color="red" title="Fehler bei der Medikamentensuche" :description="errorMessage" />

    <UAlert v-else-if="warningMessage" color="amber" variant="subtle" :title="warningMessage" />

    <div v-if="drugList.items.length > 0">
      <ul>
        <li
            v-for="item in paginatedItems" :key="item.drug.id"
            class="relative border border-[#ededed] my-1 py-2 rounded-md hover:bg-[#ededed] hover:cursor-pointer"
            style="position: relative"
            @click="selectDrug(item)" @mouseover="hoveredItem = item" @mouseleave="hoveredItem = null">
          <div>
            <strong>Name: {{ item.drug.trade_name }} </strong><br>
            <div v-for="system in drugCodeSystems" :key="system.id">
              {{ system.id }}: {{ item.drug.codes?.[system.id] }}
              <UTooltip v-if="system.desc" :text="system.desc" :popper="{ placement: 'right' }">
                <UIcon name="i-heroicons-question-mark-circle" class="w-4 h-4 text-black cursor-pointer" />
              </UTooltip>
            </div>
            <div v-for="attr in drugFieldDefinitionsObject.attrs" :key="attr[1]">
              {{ attr[0] }}: {{ item.drug?.attrs?.[attr[1]] }}
              <UTooltip v-if="attr[3]" :text="attr[3]" :popper="{ placement: 'right' }">
                <UIcon name="i-heroicons-question-mark-circle" class="w-4 h-4 text-black cursor-pointer" />
              </UTooltip>
            </div>
            <div v-for="attr_ref in drugFieldDefinitionsObject.attrs_ref" :key="attr_ref[1]">
              {{ attr_ref[0] }}: {{ item.drug?.attrs_ref?.[attr_ref[1]]?.display }}
              <UTooltip v-if="attr_ref[3]" :text="attr_ref[3]" :popper="{ placement: 'right' }">
                <UIcon name="i-heroicons-question-mark-circle" class="w-4 h-4 text-black cursor-pointer" />
              </UTooltip>
            </div>
          </div>
          <div
              v-if="hoveredItem === item"
              class="absolute top-1/2 -translate-y-1/2 right-full w-1/2 mx-10 bg-[#f9f9f9] border border-[#ededed] rounded-md py-2 px-4">
            <div v-for="attr_multi_ref in drugFieldDefinitionsObject.attrs_multi_ref" :key="attr_multi_ref[1]">
              <span class="text-sm font-bold">{{ attr_multi_ref[0] }}:</span> <span class="text-sm">{{
                item.drug?.attrs_multi_ref?.[attr_multi_ref[1]][0]?.display }}</span>
            </div>
          </div>
        </li>
      </ul>
      <div v-if="drugList.count >= 6" class="pagination">
        <div class="flex flex-row justify-center space-x-2">
          <button
              class="border border-black py-1 px-2 rounded-lg hover:bg-slate-100"
              @click="state.currentPage > 1 ? state.currentPage-- : 0"
          >
            &lt;
          </button>
          <button
              class="border border-black py-1 px-2 rounded-lg hover:bg-slate-100 mx-10"
              @click="state.currentPage < totalPages ? state.currentPage++ : 0"
          >
            &gt;
          </button>
        </div>
        <p class="text-lg mt-2">Page {{ state.currentPage }} of {{ totalPages }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, reactive } from "vue";
import { apiGetFieldDefinitions, apiDrugSearch } from '~/api/drug';
import { useMedlogapi } from '#imports';

defineProps({
  autofocusInput: { type: Boolean, default: false },
});

const emit = defineEmits(['drug-selected'])

const { data: codeSystems } = await useMedlogapi("/api/drug/code_def")
const drugCodeSystems = codeSystems.value.filter((item) => item.client_visible === true)

const drugFieldDefinitionsObject = await apiGetFieldDefinitions("search_result")

const hoveredItem = ref(null);

const state = reactive({
  searchTerm: "",
  currentPage: 1,
  itemsPerPage: 5,
});

const drugList = reactive({
  items: [],
  count: 0,
});

const errorMessage = ref("");
const isLoading = ref(false);
const warningMessage = ref("");

const fetchDrugs = async (searchTerm) => {
  errorMessage.value = ""
  isLoading.value = true;
  try {
    warningMessage.value = ''
    const response = await apiDrugSearch(searchTerm)

    if (response.total_count === 0) {
      warningMessage.value = `Kein Medikament zur Eingabe "${searchTerm}" gefunden`
    }

    drugList.items = response.items || [];
    drugList.count = response.count || 0;
    state.currentPage = 1;
  } catch (error: any) {
    console.error("Error fetching drugs:", error);
    console.log(error.detail);

    errorMessage.value = error?.data?.detail || error?.message || "Unbekannter Fehler beim Laden, bitte wenden Sie sich an Ihren Admin"
    drugList.items = [];
    drugList.count = 0;
  } finally {
    isLoading.value = false;
  }
};

watch(
  () => state.searchTerm,
  (newValue) => {
    if (newValue && newValue.length >= 3) {
      fetchDrugs(newValue);
    } else if (newValue === "") {
      warningMessage.value = "";
    }
  },
  { immediate: false }
);

const paginatedItems = computed(() => {
  const startIndex = (state.currentPage - 1) * state.itemsPerPage;
  const endIndex = startIndex + state.itemsPerPage;
  return drugList.items.slice(startIndex, endIndex);
});

const totalPages = computed(() => {
  return Math.ceil(drugList.count / state.itemsPerPage);
});

function selectDrug(item) {
  state.searchTerm = "";
  console.log('drug selected', item.drug_id);
  emit('drug-selected', item.drug_id);
}
</script>

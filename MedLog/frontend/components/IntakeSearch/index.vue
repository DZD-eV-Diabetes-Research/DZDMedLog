<template>
  <UIBaseCard :naked="true">
    <UFormGroup label="Medikament" name="drug" required>
      <UInput v-model="state.drug" placeholder="Medikament/PZN oder ATC-Code eingeben"
        icon="i-heroicons-magnifying-glass-20-solid" :color="props.color" />
    </UFormGroup>
    <div v-if="isLoading && props.edit && !props.custom">
      <UProgress animation="elastic" color="blue" class="my-6" />
    </div>
    <div v-if="isLoading && props.edit && props.custom">
      <UProgress animation="elastic" color="yellow" class="my-6" />
    </div>
    <div>
      <div v-if="drugList.items.length > 0">
        <ul>
          <li @click="printMedication(item)"
            class="relative border border-[#ededed] my-1 py-2 rounded-md hover:bg-[#ededed] hover:cursor-pointer"
            v-for="item in paginatedItems" :key="item.drug.id" @mouseover="hoveredItem = item"
            @mouseleave="hoveredItem = null" style="position: relative">
            <div>
              <strong>Name: {{ item.drug.trade_name }} </strong><br />
              PZN: {{ item.drug.codes.PZN }} <br />
              <div v-for="attr in drugFieldDefinitionsObject.attrs" :key="attr[1]">
                {{ attr[0] }}: {{ item.drug?.attrs?.[attr[1]] }}
              </div>
              <div v-for="attr_ref in drugFieldDefinitionsObject.attrs_ref" :key="attr_ref[1]">
                {{ attr_ref[0] }}: {{ item.drug?.attrs_ref?.[attr_ref[1]]?.display }}
              </div>
            </div>
            <div
              class="absolute top-1/2 -translate-y-1/2 right-full w-1/2 mx-10 bg-[#f9f9f9] border border-[#ededed] rounded-md py-2 px-4"
              v-if="hoveredItem === item">
              <div v-for="attr_multi_ref in drugFieldDefinitionsObject.attrs_multi_ref" :key="attr_multi_ref[1]">
                <span class="text-sm font-bold">{{ attr_multi_ref[0] }}:</span> <span class="text-sm">{{
                  item.drug?.attrs_multi_ref?.[attr_multi_ref[1]][0]?.display }}</span>
              </div>
            </div>
          </li>
        </ul>
        <div class="pagination" v-if="drugList.count >= 6">
          <div class="flex flex-row justify-center space-x-2">
            <button @click="state.currentPage > 1 ? state.currentPage-- : 0"
              class="border border-black py-1 px-2 rounded-lg hover:bg-slate-100">
              < </button>
                <button @click="state.currentPage < totalPages ? state.currentPage++ : 0"
                  class="border border-black py-1 px-2 rounded-lg hover:bg-slate-100 mx-10">
                  >
                </button>
          </div>
          <p class="text-lg mt-2">Page {{ state.currentPage }} of {{ totalPages }}</p>
        </div>
      </div>
      <div v-if="drugList.count == 0 && state.drug.length >= 3 && showMissingDrugOnLoad" class="text-center my-6">
        <h4>
          Es konnte kein Medikament zu folgender Eingabe gefunden werden:
        </h4>
        <h3 class="text-2xl my-2">{{ state.drug }}</h3>
      </div>

      <div v-if="fetchError" class="text-center my-6">
        <h4 class="text-red-500 text-xl">
          Beim Laden der Medikamente trat folgender Fehler auf:
        </h4>
        <h4 class="mt-2 text-red-500 text-xl">
          {{ fetchError }}
        </h4>
      </div>

      <div v-if="props.custom && !drugStore.item">
        <h3>{{ customDrug }}</h3>
      </div>
    </div>
    <div v-if="drugStore.item" class="my-8">
      <p>Medikament: {{ drugStore.item.drug.trade_name }}</p>
      <p>PZN: {{ drugStore.item.drug.codes?.PZN }}</p>
      <p>Packungsgroesse: {{ drugStore.item.drug.attrs?.amount || 'N/A' }}</p>
      <p>
        Darreichungsform: {{ drugStore.item.drug.attrs_ref.darreichungsform?.display || 'N/A' }}
      </p>
    </div>
  </UIBaseCard>
</template>

<script setup lang="ts">
import { ref, watch, reactive } from "vue";
import { apiGetFieldDefinitions, apiDrugSearch } from '~/api/drug';

let drugFieldDefinitionsObject = await apiGetFieldDefinitions("search_result")

const hoveredItem = ref(null);
const drugStore = useDrugStore();

const state = reactive({
  drug: "",
  currentPage: 1,
  itemsPerPage: 5,
});

const drugList = reactive({
  items: [],
  count: 0,
});

const isLoading = ref(true);
const initialLoad = ref(true);
const customDrug = ref();
const showMissingDrugOnLoad = ref(false)
const fetchError = ref("")

const fetchDrugs = async () => {
  if (props.custom && initialLoad.value) {
    customDrug.value = state.drug;
    fetchError.value = ""
    if (state.drug.length >= 3) {
      try {
        showMissingDrugOnLoad.value = false
        const response = await apiDrugSearch(state.drug)

        if (response.items == 0) {
          showMissingDrugOnLoad.value = true
        }

        if (props.edit && initialLoad.value) {
          printMedication(response.items.at(-1));
          state.drug = ""
          initialLoad.value = false;
          isLoading.value = false;
          return;
        }
        drugList.items = response.items || [];
        drugList.count = response.count || 0;
        state.currentPage = 1;
      } catch (error: any) {
        console.error("Error fetching drugs:", error);
        fetchError.value = error?.data?.detail || error?.message || "Unbekannter Fehler beim Laden, bitte wenden Sie sich an Ihren Admin"
        drugList.items = [];
        drugList.count = 0;
      }
    }
  } else {
    if (state.drug.length >= 3) {
      try {
        showMissingDrugOnLoad.value = false
        const response = await apiDrugSearch(state.drug)

        if (response.items == 0) {
          showMissingDrugOnLoad.value = true
        }

        if (props.edit && initialLoad.value) {
          printMedication(response.items[0]);
          state.drug = ""
          initialLoad.value = false;
          isLoading.value = false;
          return;
        }
        drugList.items = response.items || [];
        drugList.count = response.count || 0;
        state.currentPage = 1;
      } catch (error: any) {
        console.error("Error fetching drugs:", error);
        console.log(error.detail);
        
        fetchError.value = error?.data?.detail || error?.message || "Unbekannter Fehler beim Laden, bitte wenden Sie sich an Ihren Admin"
        drugList.items = [];
        drugList.count = 0;
      }
    } else {
      drugList.items = [];
      drugList.count = 0;
    }
  }
};

watch(
  () => state.drug,
  (newValue) => {
    fetchDrugs(newValue);
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

function printMedication(item) {
  drugStore.item = item;
  state.drug = "";
}

const props = defineProps<{
  drug?: string;
  edit?: boolean;
  custom?: boolean;
  color?: string;
}>();

watch(
  () => props.drug,
  (newDrug) => {
    if (newDrug) {
      state.drug = newDrug;
      if (!initialLoad.value) {
        fetchDrugs();
      }
    }
  },
  { immediate: true }
);
</script>
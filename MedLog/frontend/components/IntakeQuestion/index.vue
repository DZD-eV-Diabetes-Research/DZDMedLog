<template>
  <UIBaseCard :naked="true">
    <UFormGroup label="Medikament" name="drug" required>
      <UInput
        v-model="state.drug"
        placeholder="Medikament/PZN oder ATC-Code eingeben"
        icon="i-heroicons-magnifying-glass-20-solid"
        :color="props.color"
      />
    </UFormGroup>
    <div v-if="isLoading && props.edit && !props.custom">
      <br />
      <UProgress animation="elastic" color="blue" />
      <br />
    </div>
    <div>
      <div v-if="drugList.items.length > 0">
        <ul>
          <li
            @click="printMedication(item)"
            class="drug"
            v-for="item in paginatedItems"
            :key="item.pzn"
            @mouseover="hoveredItem = item"
            @mouseleave="hoveredItem = null"
            style="position: relative"
          >
            Name: {{ item.item.name }} <br />
            PZN: {{ item.pzn }} <br />
            Größe: {{ item.item.packgroesse }}
            <div
              class="info"
              v-if="hoveredItem === item"
              :style="{ left: '-21%', top: '-10%' }"
            >
              <p><strong>Darreichungsform</strong></p>
              <p>{{ item.item.darrform_ref.bedeutung }}</p>
              <p><strong>Applikationsform</strong></p>
              <p>{{ item.item.appform_ref.bedeutung }}</p>
            </div>
          </li>
        </ul>
        <div class="pagination" v-if="drugList.count >= 6">
          <button @click="state.currentPage > 1 ? state.currentPage-- : 0">
            Previous
          </button>
          <button
            @click="state.currentPage < totalPages ? state.currentPage++ : 0"
          >
            Next
          </button>
          <p>Page {{ state.currentPage }} of {{ totalPages }}</p>
        </div>
      </div>
      <div
        v-if="drugList.count == 0 && state.drug.length >= 3"
        style="text-align: center"
      >
        <div v-if="!initialLoad">
          <h4>
            Es konnte kein Medikament zu folgender Eingabe gefunden werden:
          </h4>
          <h3>{{ state.drug }}</h3>
        </div>
      </div>
      <div v-if="props.custom && !drugStore.item">
        <h4>Custom Medikament</h4>
        <h3>{{ customDrug }}</h3>
      </div>
    </div>
    <div v-if="drugStore.item">
          <br />
          <p>Medikament: {{ drugStore.item.item.name }}</p>
          <p>PZN: {{ drugStore.item.pzn }}</p>
          <p>Packungsgroesse: {{ drugStore.item.item.packgroesse }}</p>
          <p>
            Darreichungsform: {{ drugStore.item.item.darrform_ref.bedeutung }}
          </p>
          <p>
            Applikationsform: {{ drugStore.item.item.appform_ref.bedeutung }}
          </p>
        </div>
  </UIBaseCard>
</template>

<script setup lang="ts">
import { ref, watch, reactive } from "vue";

const hoveredItem = ref(null);
const tokenStore = useTokenStore();
const drugStore = useDrugStore();
const runtimeConfig = useRuntimeConfig();

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

const fetchDrugs = async (edit: boolean, custom: boolean) => {
  if (props.custom && initialLoad.value) {
    initialLoad.value = false;
    customDrug.value = state.drug;
    state.drug = "";
    return;
  } else {
    if (state.drug.length >= 3) {
      try {
        const response = await fetch(
          `${runtimeConfig.public.baseURL}/drug/search?search_term=${state.drug}&only_current_medications=true&offset=0&limit=100`,
          {
            method: "GET",
            headers: { Authorization: "Bearer " + tokenStore.access_token },
          }
        );
        if (!response.ok) throw new Error("Failed to fetch");
        const data = await response.json();

        if (props.edit && initialLoad.value) {
          printMedication(data.items[0]);
          state.drug = ""
          initialLoad.value = false;
          isLoading.value = false;
          return;
        }
        drugList.items = data.items || [];
        drugList.count = data.count || 0;
        state.currentPage = 1;
      } catch (error) {
        console.error("Error fetching drugs:", error);
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

<style scoped>
.pagination {
  text-align: center;
  margin-top: 15px;
  margin-bottom: 15px;
}

.drug:hover {
  background-color: #ededed;
  cursor: pointer;
  border-radius: 4px;
}

.drug {
  border-radius: 4px;
  border: 1px solid;
  border-color: #ededed;
  margin-top: 5px;
  text-align: center;
}

.info {
  position: absolute;
  background-color: rgba(237, 237, 237, 0.5);
  color: rgba(0, 0, 0, 0.75);
  font-size: 0.8rem;
  text-align: center;
  padding: 5px 10px;
  border-radius: 6px;
  z-index: 1;
  visibility: hidden;
}

.drug:hover .info {
  visibility: visible;
}
</style>

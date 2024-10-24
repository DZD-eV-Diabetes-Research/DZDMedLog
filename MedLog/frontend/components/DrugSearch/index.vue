<template>
        <UIBaseCard>
            <UFormGroup label="Medikament" name="drug">
                <UInput v-model="state.drug" placeholder="Medikament/PZN oder ATC-Code eingeben" icon="i-heroicons-magnifying-glass-20-solid"/>
            </UFormGroup>
            <div v-if="drugList.items.length > 0">
                <ul>
                    <li @click="printMedication(item)" class="drug" v-for="item in paginatedItems" :key="item.pzn"
                        @mouseover="hoveredItem = item"
                        @mouseleave="hoveredItem = null"
                        style="position: relative;">
                        Name: {{ item.item.name }} <br>
                        PZN: {{ item.pzn }} <br>
                        Größe: {{ item.item.packgroesse }}
                        <div class="info" v-if="hoveredItem === item"
                        :style="{ left: '-21%', top:'-10%'}">
                        <p><strong>Sta-Name</strong></p>
                        <p>{{item.item.staname}}</p>
                        <p><strong>Hersteller</strong></p>
                        <p>{{ item.item.hersteller_ref.bedeutung }}</p>
                    </div>
                    </li>
                </ul>
                <div class="pagination">
                    <button @click="state.currentPage > 1 ? state.currentPage-- : 0">Previous</button>
                    <button @click="state.currentPage < totalPages ? state.currentPage++ : 0">Next</button>
                    <p>Page {{ state.currentPage }} of {{ totalPages }}</p>
                </div>
            </div>
            <div v-if="drugList.count == 0 && state.drug.length >= 3" style="text-align: center;">
                <h4>Es konnte kein Medikament zu folgender Eingabe gefunden werden:</h4>
                <h3>{{ state.drug }}</h3>
            </div>
        </UIBaseCard>
        <UIBaseCard v-if="myDrugs.length > 0">
            <h3 style="text-align: center;">Meine Lieblingsdrogen</h3>
            <ul>
                <li class="drug"
                    @click="removeItem(item)"
                    v-for="item in myDrugs" :key="item.pzn">
                    Name: {{ item.item.name }} <br>
                    PZN: {{ item.pzn }} <br>
                    Größe: {{ item.item.packgroesse }}
                </li>
            </ul>
        </UIBaseCard>
</template>

<script setup lang="ts">
import { ref, watch, reactive } from 'vue';

const hoveredItem = ref(null);
const tokenStore = useTokenStore()
const runTimeConfig = useRuntimeConfig();

const state = reactive({
    drug: '',
    currentPage: 1,
    itemsPerPage: 5
});

const drugList = reactive({
    items: [],
    count: 0
});

let myDrugs = ref([]);

const fetchDrugs = async () => {
    if (state.drug.length >= 3) {
        try {
            const response = await fetch(`${runTimeConfig}/drug/search?search_term=${state.drug}&only_current_medications=true&offset=0&limit=100`, {
                method: "GET",
                headers: { 'Authorization': "Bearer " + tokenStore.access_token },
            });

            if (!response.ok) throw new Error('Failed to fetch');
            const data = await response.json();
            drugList.items = data.items || [];
            drugList.count = data.count || 0;
            state.currentPage = 1
        } catch (error) {
            console.error('Error fetching drugs:', error);
            drugList.items = [];
            drugList.count = 0;
        }
    } else {
        drugList.items = [];
        drugList.count = 0;
    }
};

watch(() => state.drug, (newValue) => {
    fetchDrugs(newValue);
}, { immediate: false });

function printMedication(item) {
    const isDuplicate = myDrugs.value.some(drug => drug.pzn === item.pzn);
    if (isDuplicate) {

    } else {
        myDrugs.value.push(item);
    }
}

function removeItem(item) {
    const index = myDrugs.value.findIndex(drug => drug.pzn === item.pzn);
    if (index !== -1) {
        myDrugs.value.splice(index, 1);
    }
}

const paginatedItems = computed(() => {
    const startIndex = (state.currentPage - 1) * state.itemsPerPage;
    const endIndex = startIndex + state.itemsPerPage;
    return drugList.items.slice(startIndex, endIndex);
});

const totalPages = computed(() => {
    return Math.ceil(drugList.count / state.itemsPerPage);
});

const props = defineProps<{ drug?: string }>();

watch(
    () => props.drug,
    (newDrug) => {
        if (newDrug) {
            state.drug = newDrug;
            fetchDrugs();
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
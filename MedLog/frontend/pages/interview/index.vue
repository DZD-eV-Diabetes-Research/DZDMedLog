<template>
    <Layout>
        <UIBaseCard>
            <UFormGroup label="Medikament" name="drug">
                <UInput v-model="state.drug" placeholder="Medikament oder PZN eingeben" />
            </UFormGroup>
            <div v-if="drugList.items.length > 0">
                <ul>
                    <li @click="printMedication(item)" class="test" v-for="item in paginatedItems" :key="item.pzn"
                        style="text-align: center;">
                        Name: {{ item.item.name }} <br>
                        PZN: {{ item.pzn }} <br>
                        Größe: {{ item.item.packgroesse }}
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
                <li @click="removeItem(item)"
                    class="test" v-for="item in myDrugs" :key="item.pzn"
                    style="text-align: center;">
                    Name: {{ item.item.name }} <br>
                    PZN: {{ item.pzn }} <br>
                    Größe: {{ item.item.packgroesse }}
                </li>
            </ul>
        </UIBaseCard>
    </Layout>
</template>

<script setup lang="ts">
import { ref, watch, reactive } from 'vue';

function printMedication(item) {
    if (myDrugs.value.includes(item)){
    } else {
    myDrugs.value.push(item)
}
}

function removeItem(item){    
    const index = myDrugs.value.findIndex(drug => drug.pzn === item.pzn);
    if (index !== -1) {
        myDrugs.value.splice(index, 1);
    }
}

const tokenStore = useTokenStore()

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

const paginatedItems = computed(() => {
    const startIndex = (state.currentPage - 1) * state.itemsPerPage;
    const endIndex = startIndex + state.itemsPerPage;
    return drugList.items.slice(startIndex, endIndex);
});

const totalPages = computed(() => {
    return Math.ceil(drugList.count / state.itemsPerPage);
});


const fetchDrugs = async () => {
    if (state.drug.length >= 3) {
        try {
            const response = await fetch(`http://localhost:8888/drug/search?search_term=${state.drug}&only_current_medications=true&offset=0&limit=100`, {
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
</script>

<style scoped>
.pagination {
    text-align: center;
    margin-top: 15px;
    margin-bottom: 15px;
}

.test:hover {
    background-color: #ededed;
    cursor: pointer;
    border-radius: 4px;
}

.test {
    border-radius: 4px;
    border: 1px solid;
    border-color: #ededed;
    margin-top: 5px;
}
</style>
<template> 
    <base-card v-on:click="selectStudy(ele)" v-for="ele in studyStore.event.items.slice().reverse()" :key="ele.id" style="text-align: center">
        <h3>{{ transformString(ele.name) }}</h3>
        <p>{{ele}}</p>
        <h3>{{ele.study_id}}</h3>
        <h3>{{ ele.id }}</h3>
    </base-card>
</template>

<script setup lang="ts">

import router from '@/router.ts';
import { useStudyStore } from '@/stores/StudyStore'

const studyStore = useStudyStore()

async function selectStudy(ele: any) {
    const study = router.currentRoute.value.params.study
    router.push("/interview/" + study + "/" + ele.name)
}

function transformString(str: String) {
    let words = str.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1));
        let transformedStr = words.join(' ');
    
    return transformedStr;
}


</script>


<style lang="scss" scoped>
.base-card:hover {
    background-color: #ededed;
    cursor: pointer;
}

.button-container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100%;
}

.center {
    text-align: center;
    margin: auto;
    width: 50%;
    padding: 10px;
}
</style>
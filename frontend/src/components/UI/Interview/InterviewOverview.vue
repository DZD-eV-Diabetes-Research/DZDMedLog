<template>
    <div class="center">
        <h1>Interviews</h1>
    </div>
    <base-card v-if="!studyStore.studies">
        <h2 v-if="userStore.isAdmin">Aktuell sind keine Studien aufgelistet bitte, legen Sie eine Studie an</h2>
        <h2 v-if="!userStore.isAdmin">Aktuell sind keine Studien aufgelistet bitte, wenden Sie sich an einen Admin</h2>
    </base-card>
    <base-card v-on:click="selectStudy(study)" v-for="study in studyStore.studies.items" :key="study.id"
        style="text-align: center">
        <h3>{{ study.display_name }}</h3>
    </base-card>
</template>

<script setup lang="ts">

import router from '@/router.ts';

import { useUserStore } from '@/stores/UserStore'
import { useStudyStore } from '@/stores/StudyStore'

const userStore = useUserStore()
const studyStore = useStudyStore()

async function selectStudy(study: any) {
    studyStore.listEvents(study.id)
    router.push("/interview/" + study.name)
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
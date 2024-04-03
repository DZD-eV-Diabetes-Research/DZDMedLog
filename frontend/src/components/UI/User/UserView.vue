<template>
    <base-card style="text-align: center;">
        <h3>Hello {{ userStore.userName }}</h3>
        <div class="button-container">
            <button @click="showStudies" disabled>Interview durchführen</button>
            <button @click="showStudies">Studien</button>
            <button @click="searchMedicaments">Medikament suchen</button>
        </div>
    </base-card>
</template>

<script setup lang="ts">

import { useTokenStore } from '@/stores/TokenStore'
import { useUserStore } from '@/stores/UserStore'
import { useStudyStore } from '@/stores/StudyStore'

import router from '@/router.ts';


const tokenStore = useTokenStore()
const userStore = useUserStore()
const studyStore = useStudyStore()

function showStudies(): void {
    try {
        studyStore.listStudies()
        router.push("/studies")
    } catch (err: any) {
        console.log(err)
        tokenStore.error = err.response
    }
}

function searchMedicaments() {
    router.push("/construction")
}

</script>

<style scoped>
.button-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.button-container button {
    margin-bottom: 35px;
}
</style>
<template>
    <Layout>
        <UIBaseCard style="text-align:center">
        <h3>Hello {{userStore.userName}}</h3>
        <div class="button-container">
            <button @click="conductInterview()">Interview durchführen</button>
            <button @click="showStudies()">Studien Verwaltung</button>
            <!-- <button @click="searchMedicaments()">Medikament suchen</button> -->
        </div>
    </UIBaseCard>
    </Layout>
</template>

<script setup lang="ts">

const userStore = useUserStore()
const studyStore = useStudyStore();
const router = useRouter()

async function conductInterview(url:string) {
    studyStore.listStudies()
    router.push({ path: "/interview" })
}

async function showStudies(url:string) {
    studyStore.listStudies()
    router.push({ path: "/studies" })
}

async function searchMedicaments(url:string) {
    router.push({path: "/search"})
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
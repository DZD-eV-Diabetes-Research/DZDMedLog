import { UIBaseButton } from '../../.nuxt/components';
<template>
    <Layout>
        <UIBaseCard style="text-align:center">
            <h3 style="margin: 5%;">Hello {{ userStore.userName }}</h3>
            <div class="button-container">
                <UIBaseButton @click="conductInterview()">Interview durchführen</UIBaseButton>
                <UIBaseButton @click="showStudies()">Studien Verwaltung</UIBaseButton>
            </div>
        </UIBaseCard>
    </Layout>
</template>

<script setup lang="ts">

const userStore = useUserStore()
const studyStore = useStudyStore();
const router = useRouter()

async function conductInterview() {
    studyStore.listStudies()
    router.push({ path: "/interview" })
}

async function showStudies() {
    studyStore.listStudies()
    router.push({ path: "/studies" })
}

// async function searchMedicaments(url:string) {
//     router.push({path: "/search"})
// }

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
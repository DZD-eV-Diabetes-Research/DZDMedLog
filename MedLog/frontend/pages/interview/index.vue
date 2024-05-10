<template>
    <Layout>
        <div class="center">
        <h1>Interviews</h1>
        </div>
        <UIBaseCard v-if="!studyStore.studies">
            <h2 v-if="userStore.isAdmin">Aktuell sind keine Studien aufgelistet bitte, legen Sie eine Studie an</h2>
            <h2 v-if="!userStore.isAdmin">Aktuell sind keine Studien aufgelistet bitte, wenden Sie sich an einen Admin</h2>
        </UIBaseCard>
        <UIBaseCard @click="selectStudy(study)" v-for="study in studyStore.studies.items" :key="study.id"
        style="text-align: center">
        <h3>{{ study.display_name }}</h3>
        </UIBaseCard>
    </Layout>
</template>

<script setup lang="ts">

const userStore = useUserStore()
const studyStore = useStudyStore()
const router = useRouter()

function selectStudy(study){
    router.push({ path: "/interview/" + study.id })
}

</script>

<style lang="scss" scoped>
.base-card:hover {
    background-color: #ededed;
    cursor: pointer;
}

.center {
    text-align: center;
    margin: auto;
    width: 50%;
    padding: 10px;
}
</style>
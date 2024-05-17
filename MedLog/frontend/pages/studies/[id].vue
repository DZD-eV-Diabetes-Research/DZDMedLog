<template>
    <Layout>
        <div class="center">
            <h3>{{ study.display_name }}</h3>
        </div>
        <UIBaseCard v-for="interview in interviews" v-if="interviews.length > 0">
            <h5>Interview Number: {{ interview.interview_number }}</h5>
            <p>Probanden-ID: {{ interview.proband_external_id }}</p>
        </UIBaseCard>
        <UIBaseCard v-else>
            <h5>Keine Interviews in Studie aufgezeichnet</h5>
        </UIBaseCard>
    </Layout>    
</template>

<script setup lang="ts">

const studyStore = useStudyStore()
const tokenStore = useTokenStore()

const route = useRoute()
const study = await studyStore.getStudy(route.params.id)

const { data: interviews, refresh } = await useFetch(`http://localhost:8888/study/${route.params.id}/interview`, {
    method: "GET",
    headers: { 'Authorization': "Bearer " + tokenStore.access_token },
})

</script>

<style scoped>

.center {
    text-align: center;
    margin: auto;
    width: 50%;
    padding: 10px;
}

</style>
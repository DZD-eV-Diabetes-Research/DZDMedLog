<template>
    <Layout>
        <UIBaseCard style="text-align: center">
            <h3>{{ study.display_name }}</h3>
            <p>{{ study }}</p>
        </UIBaseCard>
    </Layout>    
</template>

<script setup lang="ts">

const studyStore = useStudyStore()

const route = useRoute()
const study = await studyStore.getStudy(route.params.id)


</script>

<style scoped>
</style>
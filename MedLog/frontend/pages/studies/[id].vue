<template>
    <Layout>
        <UIBaseCard style="text-align: center">
            <h3>{{ study.display_name }}</h3>
        </UIBaseCard>
    </Layout>    
</template>

<script setup lang="ts">

const studyStore = useStudyStore()

const route = useRoute()
const study = studyStore.getStudy(route.params.id)


</script>

<style scoped>
</style>
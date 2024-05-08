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

const study = computed(() => {
    const studyId = route.params.id;
    return studyStore.studies.items.find(({ id }: { id: string }) => id === studyId);
});

function test(){
    console.log("test");
}

</script>

<style scoped>
.base-card:hover {
    background-color: #ededed;
    cursor: pointer;
}
</style>
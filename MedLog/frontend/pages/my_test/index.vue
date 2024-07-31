<template>
  <Layout>
    <IntakeQuestion color="blue"/>
    <DrugForm color="blue" :edit="false" :custom="false"/>
    {{drugStore}}
  </Layout>
</template>

<script setup lang="ts">
const drugStore = useDrugStore();

</script>

<style scoped>
/* Add any additional scoped styles here */
</style>

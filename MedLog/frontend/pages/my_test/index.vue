<template>
  <Layout>
    <UIBaseCard>
    <button @click="download">Download this</button>
  </UIBaseCard>
  </Layout>
</template>

<script setup lang="ts">

  const studyId = "b77b0e8b-85c0-429f-b2c0-7e617aebf682"

  async function download () {
    console.log(studyId)
  }
</script>

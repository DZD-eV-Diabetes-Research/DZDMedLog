<template>
  <div class="mt-8 w-11/12 lg:w-8/12 xl:w-6/12 mx-auto">
    <h1 class="text-4xl font-normal text-center mb-4">Übersicht</h1>

    <ul v-if="studyStore.studies.length" class="mt-4">
      <StudyOverviewCard v-for="study in studyStore.studies" :key="study.id" :study="study" as="li" />
    </ul>
    <UAlert v-else-if="!userStore.isAdmin" color="yellow" title="Keine Studien verfügbar" description="Dies kann auch an fehlenden Rechten liegen." />
    <UAlert v-else color="yellow" title="Keine Studien verfügbar" description="Über die Studienverwaltung können neue Studien angelegt werden." />
  </div>
</template>

<script setup lang="ts">
const studyStore = useStudyStore();
const userStore = useUserStore()
</script>

<style scoped>
li ~ li {
  margin-top: 1rem;
}
</style>

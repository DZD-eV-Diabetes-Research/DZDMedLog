<template>
  <div class="mt-8 max-w-6xl mx-auto">
    <h1 class="text-4xl font-normal text-center">Übersicht</h1>

    <ul v-if="studyStore.studies" class="mt-4">
      <StudyOverviewCard v-for="study in studyStore.studies" :key="study.id" :study="study" as="li" />
    </ul>
    <UAlert v-else-if="!userStore.isAdmin" title="Keine Studien verfügbar" description="Dies kann auch an fehlenden Rechten liegen" />
    <UAlert v-else description="Es sind keine Studien verfügbar" />
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

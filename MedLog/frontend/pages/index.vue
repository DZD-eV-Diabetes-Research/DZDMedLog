<template>
  <div class="mt-8 w-11/12 lg:w-8/12 xl:w-6/12 mx-auto">
    <h1 class="text-4xl font-normal text-center mb-4">Interview durchführen</h1>

    <ul v-if="activeStudies.length" class="mt-4">
      <StudyOverviewCard v-for="study in activeStudies" :key="study.id" :study="study" as="li" />
    </ul>
    <WarningMessage v-else-if="!userStore.isLoggedIn" title="Nicht angemeldet" description="Bitte loggen Sie sich ein." />
    <WarningMessage v-else-if="!userStore.isAdmin" title="Keine Studien verfügbar" description="Dies kann auch an fehlenden Rechten liegen." />
    <WarningMessage v-else title="Keine Studien verfügbar" description="Über die Studienverwaltung können neue Studien angelegt werden." />
  </div>
</template>

<script setup lang="ts">
const studyStore = useStudyStore();
const userStore = useUserStore()

const activeStudies = computed(() => {
  return studyStore.activeStudies;
});
</script>

<style scoped>
li ~ li {
  margin-top: 1rem;
}
</style>

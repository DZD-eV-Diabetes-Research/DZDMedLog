<template>
  <div class="mt-8 w-11/12 lg:w-8/12 xl:w-6/12 mx-auto">
    <h1 class="text-4xl font-normal text-center mb-4">Interview durchführen</h1>

    <ul v-if="myStudies.length" class="mt-4">
      <StudyOverviewCard v-for="study in myStudies" :key="study.id" :study="study" as="li" />
    </ul>
    <WarningMessage v-else-if="!userStore.isLoggedIn" title="Nicht angemeldet" description="Bitte loggen Sie sich ein." />
    <WarningMessage v-else-if="!userStore.isAdmin" title="Keine Studien verfügbar" description="Dies kann auch an fehlenden Rechten liegen." />
    <WarningMessage v-else title="Keine Studien verfügbar" description="Über die Studienverwaltung können neue Studien angelegt werden." />
  </div>
</template>

<script setup lang="ts">
import type {SchemaStudyApiRead} from "#open-fetch-schemas/medlogapi";

const studyStore = useStudyStore();
const userStore = useUserStore()

const myStudies = computed(() => {
  function sortStudiesByName(a: SchemaStudyApiRead, b: SchemaStudyApiRead) {
    return a.display_name!.localeCompare(b.display_name!);
  }

  const activeStudies = studyStore.activeStudies;
  const deactivatedStudies = studyStore.deactivatedStudies;
  return activeStudies.sort(sortStudiesByName).concat(deactivatedStudies.sort(sortStudiesByName));
});
</script>

<style scoped>
li ~ li {
  margin-top: 1rem;
}
</style>

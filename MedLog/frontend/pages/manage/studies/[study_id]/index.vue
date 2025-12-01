<script setup lang="ts">
import type { StudyFormSchema } from "~/components/StudyManagement/Form.vue";

const route = useRoute();
const studyStore = useStudyStore();
const toast = useToast();
const userStore = useUserStore();

const studyId = route.params.study_id;

const studyToEdit = ref();

async function onCancel() {
  await navigateTo('/manage/studies');
}

async function onSubmit(data: StudyFormSchema) {
  try {
    const updatedStudy = await usePatchStudy(studyId, data);
    studyStore.upsertStudy(updatedStudy);
    await navigateTo('/manage/studies')
  } catch (error) {
    toast.add({
      title: "Fehler beim Speichern",
      description: error.data?.detail ?? error.message ?? error,
    });
  }
}

onBeforeMount(async () => {
  studyToEdit.value = studyStore.getStudy(studyId);
});
</script>

<template>
  <section v-if="userStore.isAdmin" class="container w-11/12 lg:w-8/12 xl:w-6/12 mx-auto mt-8">
    <h1 class="text-4xl font-normal text-center mb-4">Studie bearbeiten</h1>

    <StudyManagementForm
        :initial-state="studyToEdit"
        @cancel="onCancel"
        @save="onSubmit"
    />
  </section>
  <section v-else class="container w-11/12 lg:w-8/12 xl:w-6/12 mx-auto mt-8">
    <ErrorMessage
        title="Keine Berechtigung"
        message="Ihnen fehlt die Berechtigung für diese Seite"
    />
  </section>
</template>

<style scoped>

</style>

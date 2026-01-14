<template>
  <section v-if="userStore.isAdmin" class="container w-11/12 lg:w-8/12 xl:w-6/12 mx-auto mt-8">
    <h1 class="text-4xl font-normal text-center mb-4">Studienverwaltung</h1>

    <p class="my-4 text-center text-gray-500">
      Hier können Studien, deren Events und Zugriffsberechtigungen verwaltet werden.
    </p>

    <div class="flex flex-row justify-end">
      <UButton
          label="Studie anlegen"
          icon="i-heroicons-plus"
          :disabled="!userStore.isAdmin"
          @click="openStudyModal()" />
    </div>

    <StudyManagementTable :studies="studyStore.studies"/>

    <CreateStudyModal v-model="createStudyModalVisible" class="w-[1000px] !important" @create-study="createStudy">
      <template #error>
        <ErrorMessage v-if="createStudyErrorMessage" title="Konnte Studie nicht anlegen" :message="createStudyErrorMessage" />
      </template>
    </CreateStudyModal>
  </section>
  <section v-else class="container w-11/12 lg:w-8/12 xl:w-6/12 mx-auto mt-8">
    <ErrorMessage
        title="Keine Berechtigung"
        message="Ihnen fehlt die Berechtigung für diese Seite"
    />
  </section>
</template>

<script setup lang="ts">
import {
  onMounted,
  ref,
  useCreateStudy,
  useStudyStore,
  useUserStore
} from "#imports";

const userStore = useUserStore();
const studyStore = useStudyStore();

const createStudyModalVisible = ref(false);
const createStudyErrorMessage = ref();

async function openStudyModal() {
  createStudyModalVisible.value = true
  createStudyErrorMessage.value = ""
}

async function createStudy(name: string) {
  try {
    const newStudy = await useCreateStudy(name);
    studyStore.upsertStudy(newStudy);
    createStudyModalVisible.value = false;
  } catch (error) {
    createStudyErrorMessage.value = error.response?._data?.detail ?? error.message ?? error;
  }
}

onMounted(() => {
  studyStore.loadAvailableStudies();
});
</script>

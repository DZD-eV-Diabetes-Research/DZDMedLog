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

    <StudyManagementTable
        :studies="studyStore.studies"
        @edit-permissions="(studyId) => openStudyPermissionModal(studyId)"
    />

    <UModal v-model="showModal" class="w-[1000px] !important">
      <div class="p-4 text-center">
        <UForm :schema="schema" :state="state" class="space-y-4" @submit="createStudy">
          <h3 class="text-2xl font-normal">Studie anlegen</h3>
          <ErrorMessage v-if="errorMessage" title="Konnte Studie nicht anlegen" :message="errorMessage" />
          <UFormGroup label="Studienname" name="study_name">
            <UInput v-model="state.study_name" required />
          </UFormGroup>
          <UButton
              type="submit" label="Studie anlegen" color="green" variant="soft"
              class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
        </UForm>
      </div>
    </UModal>
    <UModal v-model="studyPermissionModal" :ui="{ width: 'lg:max-w-6xl' }">
      <StudyPermissionManagement :study-id="studyId" />
    </UModal>
  </section>
  <section v-else class="container w-11/12 lg:w-8/12 xl:w-6/12 mx-auto mt-8">
    <ErrorMessage
        title="Keine Berechtigung"
        message="Ihnen fehlt die Berechtigung für diese Seite"
    />
  </section>
</template>

<script setup lang="ts">
import { object, string } from "yup";

const userStore = useUserStore();
const studyStore = useStudyStore();
const { $medlogapi } = useNuxtApp();


const showModal = ref(false);
const state = reactive({
  study_name: "",
});

const schema = object({
  study_name: string().max(128).required("Required"),
});

const errorMessage = ref();

async function openStudyModal() {
  state.study_name = ""
  showModal.value = !showModal.value
  errorMessage.value = ""
}

async function createStudy() {
  try {
    const body = { display_name: state.study_name.trim() };
    await $medlogapi("/api/study", {
      method: "POST",
      body,
    });
    await studyStore.loadAvailableStudies();
    showModal.value = false;
  } catch (error) {
    errorMessage.value = error.response?._data?.detail ?? error.message ?? error;
  }
}

const studyId = ref("")
const studyPermissionModal = ref(false)
function openStudyPermissionModal(study_id: string) {
  studyPermissionModal.value = !studyPermissionModal.value
  studyId.value = study_id
}

onMounted(() => {
  studyStore.loadAvailableStudies();
});
</script>

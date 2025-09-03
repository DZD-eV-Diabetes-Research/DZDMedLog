<template>
  <Layout>
    <div class="flex flex-row justify-center mb-6">
      <h1 class="text-4xl font-medium">Studienverwaltung</h1>
    </div>
    <UIBaseCard v-if="!studyStore.studies">
      <h2 v-if="userStore.isAdmin">
        Aktuell sind keine Studien aufgelistet bitte, legen Sie eine Studie an
      </h2>
      <h2 v-if="!userStore.isAdmin">
        Aktuell sind keine Studien aufgelistet bitte, wenden Sie sich an einen
        Admin
      </h2>
    </UIBaseCard>
    <UIBaseCard :naked="true">
      <UButton v-if="userStore.isAdmin" @click="openStudyModal()" label="Studie anlegen" color="green" variant="soft"
        class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
      <UTooltip v-if="!userStore.isAdmin" text="Sie haben keine Adminrechte">
        <UButton v-if="!userStore.isAdmin" label="Studie anlegen" color="green" variant="soft"
          class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" :disabled="true" />
      </UTooltip>
      <UModal v-model="showModal" class="w-[1000px] !important">
        <div class="p-4 text-center">
          <UForm :schema="schema" :state="state" class="space-y-4" @submit="createStudy">
            <h3 class="text-2xl font-normal">Studie anlegen</h3>
            <UFormGroup label="Studienname" name="study_name">
              <UInput v-model="state.study_name" required />
            </UFormGroup>
            <h3 v-if="errorMessage" style="color: red">{{ errorMessage }}</h3>
            <UButton type="submit" label="Studie anlegen" color="green" variant="soft"
              class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
          </UForm>
        </div>
      </UModal>
    </UIBaseCard>
    <UIBaseCard v-for="study in studyStore.studies.items" :key="study.id" style="text-align: center">
      <h3 class="text-2xl font-medium my-4">Studie: {{ study.display_name }}</h3>

      <div class="flex flex-row justify-center space-x-4">
        <UButton type="button" @click="selectStudy(study)" label="Eventverwaltung" color="green" variant="soft"
          class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
        <UButton type="submit" @click="gotoExport(study.id)" label="Datenexport" color="blue" variant="soft"
          class="border border-blue-500 hover:bg-blue-300 hover:border-white hover:text-white px-4" />
        <UButton type="submit" @click="openStudyPermissionModal(study.id)" label="Studien-Zugriffsrechte" color="violet"
          variant="soft"
          class="border border-violet-500 hover:bg-violet-300 hover:border-white hover:text-white px-4" />
      </div>

    </UIBaseCard>
    <UModal v-model="studyPermissionModal" :ui="{ width: 'lg:max-w-6xl' }">
      <StudyPermissionManagement :studyId="studyId" />
    </UModal>
  </Layout>
</template>

<script setup lang="ts">
import { object, string, type InferType } from "yup";

const userStore = useUserStore();
const studyStore = useStudyStore();
const router = useRouter();
const { $medlogapi } = useNuxtApp();


const showModal = ref(false);
const state = reactive({
  study_name: "",
});

const schema = object({
  study_name: string().required("Required"),
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
    studyStore.listStudies();
    showModal.value = false;
  } catch (error) {
    if (error.response && error.response._data) {
      errorMessage.value = error.response._data.detail;
      console.log("Error detail:", errorMessage.value);
    } else {
      console.log(error);
    }
  }
}

function selectStudy(study) {
  router.push({ path: "/studies/" + study.id });
}

async function gotoExport(study_id) {
  router.push({ path: "/studies/" + study_id + "/export" });
}

const studyId = ref("")
const studyPermissionModal = ref(false)
function openStudyPermissionModal(study_id: string) {
  studyPermissionModal.value = !studyPermissionModal.value
  studyId.value = study_id
}
</script>
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
    <UIBaseCard v-if="userStore.isAdmin" :naked="true">
      <UButton @click="openModal()" label="Studie anlegen" color="green" variant="soft"
        class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
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
      </div>

    </UIBaseCard>
  </Layout>
</template>

<script setup lang="ts">
import { object, string, type InferType } from "yup";

const runtimeConfig = useRuntimeConfig();
const userStore = useUserStore();
const studyStore = useStudyStore();
const tokenStore = useTokenStore();
const router = useRouter();

const showModal = ref(false);
const state = reactive({
  study_name: "",
});

const schema = object({
  study_name: string().required("Required"),
});

const errorMessage = ref();

async function openModal() {
  state.study_name = ""
  showModal.value = !showModal.value
  errorMessage.value = ""
}

async function createStudy() {
  try {
    const body = { display_name: state.study_name.trim() };
    const data = await $fetch(runtimeConfig.public.baseURL + "study", {
      method: "POST",
      headers: { Authorization: "Bearer " + tokenStore.access_token },
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
</script>
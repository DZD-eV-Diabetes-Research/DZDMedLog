<template>
  <Layout>
    <div class="center">
      <h1>Studien</h1>
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
      <UButton
        @click="openModal()"
        label="Studie anlegen"
        color="green"
        variant="soft"
        class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white"
      />
      <UModal v-model="showModal">
        <div class="p-4" style="text-align: center">
          <UForm
            :schema="schema"
            :state="state"
            class="space-y-4"
            @submit="createStudy"
          >
            <h3>Studie anlegen</h3>
            <UFormGroup label="Studienname" name="study_name">
              <UInput v-model="state.study_name" required />
            </UFormGroup>
            <h3 v-if="errorMessage" style="color: red">{{errorMessage}}</h3>
            <UButton
              type="submit"
              label="Studie anlegen"
              color="green"
              variant="soft"
              class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white"
            />
          </UForm>
        </div>
      </UModal>
    </UIBaseCard>
    <UIBaseCard
      v-for="study in studyStore.studies.items"
      :key="study.id"
      style="text-align: center"
    >
      <h3>{{ study.display_name }}</h3>

      <div class="button-container">
      <UButton type="button"
              @click="selectStudy(study)"
              label="Eventverwaltung"
              color="green"
              variant="soft"
              class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white"/>
      <UButton type="submit"
              @click="getDownload(study.id)"
              label="Datenexport"
              color="blue"
              variant="soft"
              class="border border-blue-500 hover:bg-blue-300 hover:border-white hover:text-white"/>
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


const startedDownload = ref(false)

const {data,status,refresh} = await useFetch('')

async function getDownload(study_id) {

  try {
    await fetch(`${runtimeConfig.public.baseURL}study/${study_id}/export?format=csv`, {
      method: "POST",
      headers: {
        'Authorization': "Bearer " + tokenStore.access_token,
      },})

      startedDownload.value = true

  } catch (error) {
    console.log(error);
  }



  // const fileUrl = `${runtimeConfig.public.baseURL}study/b2afcc3c-0877-4000-acc6-82eec4955327/export/40b12eac-bad6-4036-8908-83e29b47ad86/download`;


  // try {
  //   const response = await fetch(fileUrl, {
  //     method: "GET",
  //     headers: {
  //       'Authorization': "Bearer " + tokenStore.access_token,
  //       'Accept': '*/*',
  //     },
  //   });

  //   if (response.ok) {
  //     const a = document.createElement('a');
  //     a.href = fileUrl;
  //     document.body.appendChild(a);
  //     a.click();
  //     document.body.removeChild(a);
  //   } else {
  //     console.error('Failed to download file:', response.statusText);
  //   }
  // } catch (error) {
  //   console.error('Failed to download file:', error.message);
  // }
}
</script>

<style lang="scss" scoped>

.center {
  text-align: center;
  margin: auto;
  width: 50%;
  padding: 10px;
}

.button-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  width: 52%;
  margin: 0 21%; 
}

</style>

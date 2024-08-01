<template>
  <div class="p-4">
    <UForm
      :schema="newDrugSchema"
      :state="newDrugState"
      class="space-y-4"
      @submit="createNewDrug"
    >
      <div style="text-align: center">
        <h4>
          Hiermit wird einmalig ein Medikament angelegt, das in der
          Medikamentensuche nicht gefunden wurde
        </h4>
      </div>
      <UFormGroup label="Name" name="name" required>
        <UInput v-model="newDrugState.name" color="yellow" />
      </UFormGroup>
      <UFormGroup label="Darreichungsform" name="darrform" required>
        <h5 v-if="showDarrFormError" style="color: red">
          Darreichungsform wird benötigt
        </h5>
        <UCommandPalette
          v-if="!selectedDosageForm"
          v-model="selectedDosageForm"
          :autoselect="false"
          :groups="[{ key: 'dosageFormTable', commands: dosageFormTable }]"
          :fuse="{ resultLimit: 5, fuseOptions: { threshold: 0.2 } }"
        />
        <p v-else @click="selectedDosageForm = null" class="selectedDarrForm">
          {{ selectedDosageForm.label }}
        </p>
      </UFormGroup>
      <UAccordion :items="customDrugForm" color="yellow">
        <template #custom-form>
          <UFormGroup label="Dosis" name="dose">
            <UInput v-model="newDrugState.dose" color="yellow" />
          </UFormGroup>
          <UFormGroup label="PZN" name="pzn">
            <UInput
              v-model="newDrugState.pzn"
              placeholder="Falls bekannt"
              color="yellow"
            />
          </UFormGroup>
          <UFormGroup label="Herstellercode" name="herstellerCode">
            <UInput
              v-model="newDrugState.herstellerCode"
              placeholder="Falls bekannt"
              color="yellow"
            />
          </UFormGroup>
          <UFormGroup label="Applikationsform" name="appform">
            <UInput
              v-model="newDrugState.appform"
              placeholder="Falls bekannt"
              color="yellow"
            />
          </UFormGroup>
          <UFormGroup label="ATC-Code" name="atc_code">
            <UInput
              v-model="newDrugState.atc_code"
              placeholder="Falls bekannt"
              color="yellow"
            />
          </UFormGroup>
          <UFormGroup label="Packungsgroesse" name="packgroesse">
            <UInput
              v-model="newDrugState.packgroesse"
              placeholder="Falls bekannt"
              color="yellow"
            />
          </UFormGroup>
        </template>
      </UAccordion>
      <div style="text-align: center">
        <UButton
          type="submit"
          color="yellow"
          variant="soft"
          class="border border-yellow-500 hover:bg-yellow-300 hover:border-white hover:text-white"
        >
          Ungelistetes Medikament Speichern
        </UButton>
      </div>
    </UForm>
  </div>
  <DrugForm color="yellow" :edit=false :custom=true label="U"/>
</template>

<script setup lang="ts">
import dayjs from "dayjs";
import { object, number, date, string, type InferType } from "yup";

// general constants

const route = useRoute();
const router = useRouter();
const tokenStore = useTokenStore();
const drugStore = useDrugStore();
const studyStore = useStudyStore();
const userStore = useUserStore();
const runtimeConfig = useRuntimeConfig();

const newDrugState = reactive({
  pzn: "",
  name: "",
  dose: 0,
  herstellerCode: "",
  darrform: "",
  appform: "",
  atc_code: "",
  packgroesse: 0,
});

const newDrugSchema = object({
  pzn: string(),
  name: string().required("Benötigt"),
  dose: number(),
  herstellerCode: string(),
  darrform: string(),
  appform: string(),
  atc_code: string(),
  packgroesse: number(),
});

const customDrugForm = [
  {
    label: "Zusätzliche Information",
    icon: "i-heroicons-information-circle",
    slot: "custom-form",
  },
];

// const customDrugModalVisibility = ref(false);

const showDarrFormError = ref(false);
const selectedDosageForm = ref();
const dosageFormTable = ref();

// async function openCustomModal() {
//   customDrugModalVisibility.value = !customDrugModalVisibility.value;
//   showDarrFormError.value = false;
// }

async function createNewDrug() {
  showDarrFormError.value = false;
  const date = dayjs(Date()).format("YYYY-MM-DD");
  const myDose = newDrugState.dose;

  try {
    const response = await $fetch(
      `${runtimeConfig.public.baseURL}drug/user-custom`,
      {
        method: "POST",
        headers: { Authorization: "Bearer " + tokenStore.access_token },
        body: {
          created_at: date,
          pzn: newDrugState.pzn ? newDrugState.pzn : null,
          name: newDrugState.name ? newDrugState.name : null,
          hersteller_code: newDrugState.herstellerCode
            ? newDrugState.herstellerCode
            : null,
          darrform: selectedDosageForm.value.darrform,
          appform: newDrugState.appform ? newDrugState.appform : null,
          atc_code: newDrugState.atc_code ? newDrugState.atc_code : null,
          packgroesse: newDrugState.packgroesse
            ? newDrugState.packgroesse
            : null,
        },
      }
    );

    const pzn = newDrugState.pzn ? newDrugState.pzn : null;
    await useCreateIntake(
      route.params.study_id,
      route.params.interview_id,
      pzn,
      null,
      date,
      null,
      null,
      null,
      myDose,
      "Yes",
      response.id
    );

    router.go();
  } catch (error) {
    console.log("Failed to create Intake: ", error);
    if (selectedDosageForm.value === undefined) {
      showDarrFormError.value = true;
    }
    if (
      error.message ===
      "Cannot read properties of undefined (reading 'darrform')"
    ) {
      showDarrFormError.value = true;
    }
  }
}

async function getDosageForm() {
  const dosageForm = await $fetch(
    `${runtimeConfig.public.baseURL}drug/enum/darrform`,
    {
      method: "GET",
      headers: { Authorization: "Bearer " + tokenStore.access_token },
    }
  );

  dosageFormTable.value = dosageForm.items.map((item) => ({
    id: item.bedeutung + " (" + item.darrform + ")",
    label: item.bedeutung + " (" + item.darrform + ")",
    bedeutung: item.bedeutung,
    darrform: item.darrform,
  }));
}

getDosageForm();
</script>

<style scoped></style>

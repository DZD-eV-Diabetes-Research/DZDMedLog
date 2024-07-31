<template>
  <Layout>
    <UIBaseCard :naked="true">
      <UButton
        @click="openIntakeForm()"
        label="Eingabe Präparat"
        color="green"
        variant="soft"
        style="margin-right: 10px"
        class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white"
      />
    </UIBaseCard>
    <div v-if="showIntakeForm">
      <UIBaseCard>
        <IntakeQuestion color="green" />
        <DrugForm color="green" :edit="false" :custom="false" label="Medikament Speichern"/>
        <!-- <UModal v-model="customDrugModalVisibility">
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
                <UInput v-model="newDrugState.name" color="yellow"/>
              </UFormGroup>
              <UFormGroup label="Darreichungsform" name="darrform" required>
                <h5 v-if="showDarrFormError" style="color: red">
                  Darreichungsform wird benötigt
                </h5>
                <UCommandPalette
                  v-if="!selectedDosageForm"
                  v-model="selectedDosageForm"
                  :autoselect="false"
                  :groups="[
                    { key: 'dosageFormTable', commands: dosageFormTable },
                  ]"
                  :fuse="{ resultLimit: 5, fuseOptions: { threshold: 0.2 } }"
                />
                <p
                  v-else
                  @click="selectedDosageForm = null"
                  class="selectedDarrForm"
                >
                  {{ selectedDosageForm.label }}
                </p>
              </UFormGroup>
              <UAccordion :items="customDrugForm" color="yellow">
                <template #custom-form>
                <UFormGroup label="Dosis" name="dose">
                  <UInput v-model="newDrugState.dose" color="yellow"/>
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
        </UModal> -->
      </UIBaseCard>
    </div>
    <div class="tableDiv">
      <h4 style="text-align: center; padding-top: 25px">Medikationshistorie</h4>
      <div>
        <div
          class="flex px-3 py-3.5 border-b border-gray-200 dark:border-gray-700"
        >
          <UInput v-model="q" placeholder="Tabelle Filtern" />
        </div>
        <UTable :rows="rows" :columns="columns">
          <template v-if="userStore.isAdmin" #actions-data="{ row }">
            <UDropdown :items="myOptions(row)">
              <UButton
                color="gray"
                variant="ghost"
                icon="i-heroicons-ellipsis-horizontal-20-solid"
              />
            </UDropdown>
          </template>
        </UTable>
        <div
          v-if="
            tableContent.length >= pageCount || filteredRows.length >= pageCount
          "
          class="flex justify-center px-3 py-3.5 border-t dark:border-green-700 dark:border-red-500"
        >
          <UPagination
            v-model="page"
            :page-count="pageCount"
            :total="filteredRows.length"
            :ui="{
              wrapper: 'flex items-center gap-1',
              rounded: 'rounded-sm',
              default: {
                activeButton: {
                  variant: 'outline',
                },
              },
            }"
          />
        </div>
      </div>
      <div style="text-align: center">
        <UButton
          @click="backToOverview()"
          label="Zurück zur Übersicht"
          color="green"
          variant="soft"
          class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white"
          style="margin: 25px"
        />
      </div>
    </div>
    <UModal v-model="deleteModalVisibility">
      <div class="p-4">
        <div style="text-align: center">
          <h4 style="color: red">Sie löschen folgenden Eintrag:</h4>
          <br />
          <h4>{{ drugToDelete.drug }}</h4>
          <br />
          <UForm
            :schema="deleteSchema"
            :state="deleteState"
            class="space-y-4"
            @submit="deleteIntake"
          >
            <UFormGroup label="Zum löschen den Namen eintragen" name="drug">
              <UInput
                v-model="deleteState.drug"
                color="red"
                :placeholder="drugToDelete.drug"
              />
            </UFormGroup>
            <br />
            <UButton
              type="submit"
              color="red"
              variant="soft"
              class="border border-red-500 hover:bg-red-300 hover:border-white hover:text-white"
            >
              Eintrag löschen
            </UButton>
          </UForm>
        </div>
      </div>
    </UModal>
    <UModal v-model="editModalVisibility" @close="drugStore.$reset()">
      <div class="p-4">
        <div style="text-align: center">
          <IntakeQuestion
            :drug="toEditDrug"
            :edit="true"
            :custom="customDrug"
            color="blue"
          />
          <DrugForm color="blue" :edit="true" :custom="false" label="Bearbeiten"/>
        </div>
      </div>
    </UModal>
  </Layout>
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

drugStore.item = null;

// Intakeform

const showIntakeForm = ref(true);

async function openIntakeForm() {
  showIntakeForm.value = !showIntakeForm.value;
}

// Editform Modal

const toEditDrug = ref();
const editModalVisibility = ref(false);

// const editSchema = object({
//   selected: string().required("Required"),
//   startTime: date().required("Required"),
//   dose: number().min(0, "Hallo"),
// });

// const editState = reactive({
//   selected: "Yes",
//   startTime: dayjs(Date()).format("YYYY-MM-DD"),
//   endTime: null,
//   dose: 0,
//   source: null,
//   intervall: null,
//   custom: null,
// });

const toEditDrugId = ref();
const customDrug = ref();

const tempIntervall = ref();
const tempDose = ref();
const tempFrequency = ref();
const my_stuff = ref();

async function editModalVisibilityFunction(row: object) {  
  
  tempIntervall.value = null;
  tempDose.value = null;
  tempFrequency.value = null;
  my_stuff.value = null;
  

  try {   
    console.log(row);
    
    drugStore.source = row.source
    drugStore.custom = row.custom;
    customDrug.value = row.custom;
    editModalVisibility.value = true;
    drugStore.intervall = row.intervall;
    tempIntervall.value = row.intervall;
    drugStore.frequency = row.intervall ? "regelmäßig" : "nach Bedarf";
    drugStore.intake_start_time_utc = row.startTime;
    drugStore.intake_end_time_utc = row.endTime;
    drugStore.dose = row.dose ? row.dose : 0;
    tempDose.value = row.dose;
    toEditDrug.value = row.drug;
    toEditDrugId.value = row.id;    
  } catch (error) {
    console.log(error);
  }
}

async function editEntry() {
  if (customDrug.value) {
    console.log(customDrug.value);
  } else {
    try {
      const fetchBody = {
        pharmazentralnummer: drugStore.item.pzn ? drugStore.item.pzn : null,
        source_of_drug_information: useDrugSourceTranslator(
          null,
          editState.source
        ),
        custom_drug_id: customDrug.value
          ? drugStore.item.item.ai_dataversion_id
          : null,
        intake_start_time_utc: editState.startTime,
        intake_end_time_utc: editState.endTime,
        administered_by_doctor: "prescribed",
        intake_regular_or_as_needed: my_stuff.value,
        dose_per_day: editState.dose,
        regular_intervall_of_daily_dose: useIntervallDoseTranslator(
          null,
          editState.intervall
        ),
        as_needed_dose_unit: null,
        consumed_meds_today: editState.selected,
      };

      await $fetch(
        `${runtimeConfig.public.baseURL}study/${route.params.study_id}/interview/${route.params.interview_id}/intake/${toEditDrugId.value}`,
        {
          method: "PATCH",
          headers: { Authorization: "Bearer " + tokenStore.access_token },
          body: fetchBody,
        }
      );

      toEditDrugId.value = null;
      editModalVisibility.value = false;
      createIntakeList();
    } catch (error) {
      console.log(error);
    }
  }
}

// Deleteform Modal

const deleteModalVisibility = ref(false);
const drugToDelete = ref();

const deleteSchema = object({
  drug: string()
    .required("Required")
    .test("is-dynamic-value", "Name muss übereinstimmen", function (value) {
      return value === drugToDelete.value.drug;
    }),
});

type DeleteSchema = InferType<typeof deleteSchema>;

const deleteState = reactive({
  drug: undefined,
});

async function openDeleteModal(row: object) {
  deleteState.drug = "";
  deleteModalVisibility.value = true;
  drugToDelete.value = row;
}

async function deleteIntake() {
  try {
    await $fetch(
      `${runtimeConfig.public.baseURL}study/${route.params.study_id}/interview/${route.params.interview_id}/intake/${drugToDelete.value.id}`,
      {
        method: "DELETE",
        headers: { Authorization: "Bearer " + tokenStore.access_token },
      }
    );
    deleteModalVisibility.value = false;
    createIntakeList();
  } catch (error) {
    console.log(error);
  }
}

// Table

const page = ref(1);
const pageCount = 15;

const rows = computed(() => {
  const data = q.value ? filteredRows.value : tableContent.value;
  return data.slice((page.value - 1) * pageCount, page.value * pageCount);
});

const columns = [
  {
    key: "pzn",
    label: "PZN",
  },
  {
    key: "drug",
    label: "Medikament",
    sortable: true,
  },
  {
    key: "source",
    label: "Quelle der Angabe",
    sortable: true,
  },
  {
    key: "dose",
    label: "Dosis",
    sortable: true,
  },
  {
    key: "intervall",
    label: "Intervall",
    sortable: true,
  },
  {
    key: "time",
    label: "Einnahme Zeitraum",
    sortable: true,
  },
  {
    key: "darr",
    label: "Darreichung",
    sortable: true,
  },
  {
    key: "actions",
  },
];

const myOptions = (row) => [
  [
    {
      label: "Bearbeiten",
      icon: "i-heroicons-pencil-square-20-solid",
      click: () => editModalVisibilityFunction(row),
    },
    {
      label: "Löschen",
      icon: "i-heroicons-trash-20-solid",
      click: () => openDeleteModal(row),
    },
  ],
];

const q = ref("");

const filteredRows = computed(() => {
  if (!q.value) {
    return tableContent.value;
  }

  return tableContent.value.filter((tableContent) => {
    return Object.values(tableContent).some((value) => {
      return String(value).toLowerCase().includes(q.value.toLowerCase());
    });
  });
});

const tableContent = ref([]);

// CustomElement Modal

const customDrugForm = [
  {
    label: "Zusätzliche Information",
    icon: "i-heroicons-information-circle",
    slot: "custom-form",
  },
];

const customDrugModalVisibility = ref(false);
const showDarrFormError = ref(false);
const selectedDosageForm = ref();
const dosageFormTable = ref();

async function openCustomModal() {
  customDrugModalVisibility.value = !customDrugModalVisibility.value;
  showDarrFormError.value = false;
}

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
  name: string().required("Required"),
  dose: number(),
  herstellerCode: string(),
  darrform: string(),
  appform: string(),
  atc_code: string(),
  packgroesse: number(),
});

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

// REST

async function backToOverview() {
  studyStore.event = "";
  router.push({
    path:
      "/interview/proband/" +
      route.params.proband_id +
      "/study/" +
      route.params.study_id,
  });
}

const { data: intakes } = useFetch(
  `${runtimeConfig.public.baseURL}study/${route.params.study_id}/proband/${route.params.proband_id}/intake/details?interview_id=${route.params.interview_id}`,
  {
    method: "GET",
    headers: { Authorization: "Bearer " + tokenStore.access_token },
  }
);

async function createIntakeList() {
  try {
    const intakes = await $fetch(
      `${runtimeConfig.public.baseURL}study/${route.params.study_id}/proband/${route.params.proband_id}/intake/details?interview_id=${route.params.interview_id}`,
      {
        method: "GET",
        headers: { Authorization: "Bearer " + tokenStore.access_token },
      }
    );    

    if (intakes && intakes.items) {
      tableContent.value = intakes.items.map((item) => ({
        pzn: item.pharmazentralnummer,
        source: useDrugSourceTranslator(item.source_of_drug_information, null),
        drug: item.drug.name,
        dose: item.dose_per_day === 0 ? "" : item.dose_per_day,
        intervall: useIntervallDoseTranslator(
          item.regular_intervall_of_daily_dose,
          null
        ),
        consumed_meds_today: item.consumed_meds_today,
        option: item.intake_regular_or_as_needed,
        startTime: item.intake_start_time_utc,
        endTime: item.intake_end_time_utc,
        time:
          item.intake_end_time_utc === null
            ? item.intake_start_time_utc + " bis unbekannt"
            : item.intake_start_time_utc + " bis " + item.intake_end_time_utc,
        darr:
          item.drug.darrform_ref.bedeutung +
          " (" +
          item.drug.darrform_ref.darrform +
          ")",
        id: item.id ? item.id : item.custom_drug_id,
        custom: item.custom_drug_id ? true : false,
        class: item.custom_drug_id
          ? "bg-yellow-500/50 dark:bg-yellow-400/50"
          : null,
      }));
    }
  } catch (error) {
    console.log(error);
  }
}

const isAction = computed(() => drugStore.isAction)

watch(isAction, (newValue) => {
  if (newValue === true) {
    createIntakeList();
    openIntakeForm()
  } else {
  }
});

getDosageForm();
createIntakeList();
</script>

<style scoped>
.newDrugButton {
  text-align: center;
  border-color: #a9e7bc;
  border-radius: 10px;
  background-color: white;
}

.new-drug-box {
  padding: 20px;
  border-style: solid;
  border-color: #adecc0;
  border-radius: 10px;
  border-width: 2px;
}

.tableDiv {
  border-radius: 10px;
  border-width: 2px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.26);
}

.selectedDarrForm:hover {
  color: #efc85d;
  cursor: pointer;
}

.flex-container {
  display: flex;
  gap: 16px;
}

.flex-container > * {
  flex: 1;
}

.custom-disabled {
  background-color: #c2c2c2;
  border-style: solid !important;
  border-color: white;
}

.custom-border input {
  color: sky;
  border-style: dotted !important;
  border-color: green !important;
}
</style>

<template>
  <Layout>
    <UIBaseCard :naked="true">
      <div class="flex flex-row justify-center">
        <CopyPreviousDrugs :onUpdate="createIntakeList"/>
      </div>
    </UIBaseCard>
    <div v-if="drugStore.intakeVisibility">
      <UIBaseCard>
        <IntakeQuestion color="green" />
        <DrugForm color="green" :edit="false" :custom="false" label="Medikament Speichern" />
        <UButton @click="openCustomModal()" label="Ungelistetes Medikament aufnehmen" color="yellow" variant="soft"
          style="margin-top: 2px"
          class="border border-yellow-500 hover:bg-yellow-300 hover:border-white hover:text-white" />
        <UModal v-model="drugStore.customVisibility">
          <div class="p-4">
            <DrugForm color="yellow" label="Ungelistetes Medikament Speichern" :custom=true :edit=false />
          </div>
        </UModal>
      </UIBaseCard>
    </div>
    <div class="tableDiv">
      <h4 style="text-align: center; padding-top: 25px">Medikationen</h4>
      <div>
        <div class="flex px-3 py-3.5 border-b border-gray-200 dark:border-gray-700">
          <UInput v-model="q" placeholder="Tabelle Filtern" />
        </div>
        <UTable :rows="rows" :columns="columns">
          <template v-if="userStore.isAdmin" #actions-data="{ row }">
            <UDropdown :items="myOptions(row)">
              <UButton color="gray" variant="ghost" icon="i-heroicons-ellipsis-horizontal-20-solid" />
            </UDropdown>
          </template>
        </UTable>
        <div v-if="
          tableContent.length >= pageCount || filteredRows.length >= pageCount
        " class="flex justify-center px-3 py-3.5 border-t dark:border-red-500">
          <UPagination v-model="page" :page-count="pageCount" :total="filteredRows.length" :ui="{
            wrapper: 'flex items-center gap-1',
            rounded: 'rounded-sm',
            default: {
              activeButton: {
                variant: 'outline',
              },
            },
          }" />
        </div>
      </div>
      <div style="text-align: center">
        <UButton @click="backToOverview()" label="Zurück zur Übersicht" color="green" variant="soft"
          class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" style="margin: 25px" />
      </div>
    </div>
    <UModal v-model="deleteModalVisibility">
      <div class="p-4">
        <div style="text-align: center">
          <h4 style="color: red">Sie löschen folgenden Eintrag:</h4>
          <br />
          <h4>{{ drugToDelete.drug }}</h4>
          <br />
          <UForm :state="deleteState" class="space-y-4" @submit="deleteIntake">
            <!-- <UFormGroup label="Zum löschen den Namen eintragen" name="drug">
              <UInput v-model="deleteState.drug" color="red" :placeholder="drugToDelete.drug" />
            </UFormGroup>
            <br /> -->
            <UButton type="submit" color="red" variant="soft"
              class="border border-red-500 hover:bg-red-300 hover:border-white hover:text-white">
              Eintrag löschen
            </UButton>
          </UForm>
        </div>
      </div>
    </UModal>
    <UModal v-model="drugStore.editVisibility" @close="drugStore.$reset()">
      <div class="p-4">
        <div style="text-align: center">
          <IntakeQuestion :drug="toEditDrug" :edit="true" :custom="customDrug"
            :color="customDrug ? 'yellow' : 'blue'" />
          <DrugForm :color="customDrug ? 'yellow' : 'blue'" :edit="true" :custom=customDrug label="Bearbeiten" />
        </div>
      </div>
    </UModal>
  </Layout>
</template>

<script setup lang="ts">
import { object, number, date, string, type InferType } from "yup";

function test() {
  console.log("Previous drugs");
}

// general constants

const route = useRoute();
const router = useRouter();
const tokenStore = useTokenStore();
const drugStore = useDrugStore();
const studyStore = useStudyStore();
const userStore = useUserStore();
const runtimeConfig = useRuntimeConfig();


drugStore.item = null;

// Editform Modal

const toEditDrug = ref();

const toEditDrugId = ref();
const customDrug = ref();

const tempIntervall = ref();
const tempDose = ref();
const tempFrequency = ref();
const my_stuff = ref();

const tableContent = ref([]);


async function editModalVisibilityFunction(row: object) {

  tempIntervall.value = null;
  tempDose.value = null;
  tempFrequency.value = null;
  my_stuff.value = null;


  try {

    drugStore.editVisibility = true
    drugStore.source = row.source
    drugStore.custom = row.custom;
    customDrug.value = row.custom;
    drugStore.intervall = row.intervall;
    tempIntervall.value = row.intervall;
    drugStore.frequency = row.intervall ? "regelmäßig" : "nach Bedarf";
    drugStore.intake_start_time_utc = row.startTime;
    drugStore.intake_end_time_utc = row.endTime;
    drugStore.dose = row.dose ? row.dose : 0;
    drugStore.darrForm = row.darr ? row.darr : null
    drugStore.drugName = row.drug ? row.drug : null
    tempDose.value = row.dose;
    drugStore.editId = row.intakeId
    toEditDrug.value = row.drug;
    toEditDrugId.value = row.intakeId;

  } catch (error) {
    console.log(error);
  }
}

// Deleteform Modal

const deleteModalVisibility = ref(false);
const drugToDelete = ref();

// const deleteSchema = object({
//   drug: string()
//     .required("Required")
//     .test("is-dynamic-value", "Name muss übereinstimmen", function (value) {
//       return value === drugToDelete.value.drug;
//     }),
// });

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
      `${runtimeConfig.public.baseURL}study/${route.params.study_id}/interview/${route.params.interview_id}/intake/${drugToDelete.value.intakeId}`,
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
    label: "Medikament PZN",
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

// CustomElement Modal

const customDrugModalVisibility = ref(false);
const showDarrFormError = ref(false);
const selectedDosageForm = ref();
const dosageFormTable = ref();

async function openCustomModal() {
  drugStore.customVisibility = !drugStore.customVisibility;
  showDarrFormError.value = false;
}

async function getDosageForm() {
  const dosageForm = await $fetch(
    `${runtimeConfig.public.baseURL}v2/drug/field_def/darreichungsform/refs`,
    {
      method: "GET",
      headers: { Authorization: "Bearer " + tokenStore.access_token },
    }
  );

  dosageFormTable.value = dosageForm.items.map((item) => ({
    id: item.display + " (" + item.value + ")",
    label: item.display + " (" + item.value + ")",
    bedeutung: item.display,
    darrform: item.value,
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
        pzn: item.drug.codes?.PZN,
        source: useDrugSourceTranslator(item.source_of_drug_information, null),
        drug: item.drug.trade_name,
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
          item.drug.attrs_ref.darreichungsform.display +
          " (" +
          item.drug.attrs_ref.darreichungsform.value +
          ")",
        intakeId: item.id,
        custom: item.drug?.custom_drug_id,
        class: item.drug?.custom_drug_id
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
  if (newValue) {
    createIntakeList();
  } else {
    createIntakeList();
    drugStore.item = ""    
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

:deep(td) {
  white-space: normal !important;
  word-break: break-word !important;
}

.selectedDarrForm:hover {
  color: #efc85d;
  cursor: pointer;
}

.flex-container {
  display: flex;
  gap: 16px;
}

.flex-container>* {
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

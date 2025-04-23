<template>
  <Layout>
    <UIBaseCard :naked="true">
      <div class="flex flex-row justify-center items-center space-x-4">
        <UButton ref="topButton" @click="saveInterview()" label="Interview Beenden" color="green" variant="soft"
          class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
        <CopyPreviousDrugs
          v-if="route.params.interview_id !== latestItems[0]?.interview_id"
          :onUpdate="createIntakeList" />
      </div>
    </UIBaseCard>
    <div v-if="drugStore.intakeVisibility">
      <UIBaseCard>
        <IntakeQuestion color="primary" />
        <DrugForm color="primary" :edit="false" :custom="false" label="Medikament Speichern" />
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
        <UButton v-if="!showScrollButton" @click="saveInterview()" label="Interview Beenden" color="green"
          variant="soft" class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white"
          style="margin: 25px" />
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
          <IntakeQuestion :drug="toEditDrug" :edit="true" :custom="customDrug === 'Nein' ? false : true"
            :color="customDrug === 'Nein' ? 'blue' : 'yellow'" />
          <DrugForm :color="customDrug === 'Nein' ? 'blue' : 'yellow'" :edit="true" :custom="customDrug === 'Nein' ? false : true" label="Bearbeiten" />
        </div>
      </div>
    </UModal>
    <UModal v-model="userStore.firstEvent" @close="resetFirstEvent()" class="custom-modal">
      <div class="p-4">
        <div style="text-align: center">
          <h3>Eingangsfrage</h3>
          <p>Wir möchten Ihre Einnahme von Diabetes-Medikamenten in den vergangegen 12 Monaten erfassen. Dazu gehören
            sowohl
            Tabletten als auch Insulinpräparate.</p>
          <br>
          <p>Außerdem bitten wir Sie um Angabe, welche anderen Medikamente Sie innerhalb der letzten 7 Tage eingenommen
            haben. Bitte denken Sie auch an Schmerzmittel und vom Arzt erhaltene Spritzen. Geben Sie Depotmittel an,
            auch
            wenn Sie diese zuletzt vor mehr als 7 Tagen eingenommen oder bekommen haben.</p>
          <br>
          <p><strong>Nur bei Frauen</strong></p>
          <p>Denken Sie bitte auch an Medikamente wie die Pille, Hormonersatzpräparate, Depotmittel oder die Spirale,
            auch
            wenn Sie diese zuletzt vor mehr als 7 Tagen eingenommen oder bekommen haben.</p>
          <br>
          <p><strong>Haben Sie Diabetes-Medikamente in den vergangenen 12 Monaten bzw. andere Medikamente in den letzten
              7
              Tagen eingenommen?</strong></p>
        </div>
      </div>
    </UModal>

  </Layout>
</template>

<script setup lang="ts">
// general constants

const route = useRoute();
const router = useRouter();
const tokenStore = useTokenStore();
const drugStore = useDrugStore();
const studyStore = useStudyStore();
const userStore = useUserStore();
const runtimeConfig = useRuntimeConfig();
const { $api } = useNuxtApp();


const { data: latestItems } = await useAPI(
  `${runtimeConfig.public.baseURL}study/${route.params.study_id}/proband/${route.params.proband_id}/interview/last/intake`,
  {
    headers: { Authorization: "Bearer " + tokenStore.access_token }
  }
);

// console.log(latestItems?.value[0].interview_id);
// console.log(route.params.interview_id)

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

    await $api(
      `${runtimeConfig.public.baseURL}study/${route.params.study_id}/interview/${route.params.interview_id}/intake/${drugToDelete.value.intakeId}`,
      {
        method: "DELETE",
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
const pageCount = 10;

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
    key: "custom",
    label: "Custom",
    sortable: true,
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
  const dosageForm = await $api(
    `${runtimeConfig.public.baseURL}v2/drug/field_def/darreichungsform/refs`);

  dosageFormTable.value = dosageForm.items.map((item) => ({
    id: item.display + " (" + item.value + ")",
    label: item.display + " (" + item.value + ")",
    bedeutung: item.display,
    darrform: item.value,
  }));
}

// REST

async function saveInterview() {

  try {
    await $api(
      `${runtimeConfig.public.baseURL}study/${route.params.study_id}/event/${route.params.event_id}/interview/${route.params.interview_id}`,
      {
        method: "PATCH",
        body: {
          "proband_external_id": `${route.params.proband_id}`,
          "interview_end_time_utc": new Date().toISOString(),
          "proband_has_taken_meds": true
        }
      }
    );
  } catch (error) {
    console.log(error);
  }

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
    const intakes = await $api(
      `${runtimeConfig.public.baseURL}study/${route.params.study_id}/proband/${route.params.proband_id}/intake/details?interview_id=${route.params.interview_id}`);

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
        custom: item.drug?.is_custom_drug ? "Ja" : "Nein",
        class: item.drug?.is_custom_drug
          ? "bg-yellow-50"
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

const resetFirstEvent = () => {
  userStore.firstEvent = false;
}

getDosageForm();
createIntakeList();

// Buttonobserver

// const topButton = ref(null);
// const showScrollButton = ref(false);
// let observer = null;

// onMounted(() => {
//   observer = new IntersectionObserver(
//     ([entry]) => {
//       showScrollButton.value = !entry.isIntersecting;
//     },
//     { threshold: 0 }
//   );

//   // Warte, bis `topButton.value` gesetzt ist
//   if (topButton.value) {
//     observer.observe(topButton.value);
//   }
// });

// onUnmounted(() => {
//   if (observer) observer.disconnect();
// });
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

.custom-modal {
  width: 20px;
}
</style>

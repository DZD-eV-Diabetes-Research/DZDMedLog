<template>
  <Layout>
    <UIBaseCard :naked="true">
      <div class="flex flex-row justify-center items-center space-x-4">
        <UButton
          ref="topButton" label="Interview Beenden" color="green" variant="soft"
          class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" @click="saveInterview()" />
        <CopyPreviousDrugs
          v-if="!pending && latestItems && route.params.interview_id !== latestItems[0]?.interview_id"
          :on-update="loadIntakeList" />
      </div>
    </UIBaseCard>
    <div>
      <UIBaseCard>
        <IntakeSearch color="primary" @drug-selected="drugId => drugForIntake = drugId" />
        <UButton
            label="Ungelistetes Medikament aufnehmen" color="yellow" variant="soft"
            class="border border-yellow-500 hover:bg-yellow-300 hover:border-white hover:text-white mt-4"
            @click="openCustomModal()"
        />
      </UIBaseCard>
      <UIBaseCard>
        <IntakeForm
            color="primary"
            :drug-id="drugForIntake"
            :edit="false"
            @save="saveIntake"
            @cancel="console.log('CANCELLED!!!!!!')"
        />
      </UIBaseCard>
      <UModal v-model="customDrugModalVisibility">
        <UCard>
          <template #header>
            Medikament anlegen
          </template>

          <UAlert
              icon="i-heroicons-information-circle"
              color="sky"
              variant="subtle"
              description="Legen Sie hier ein Medikament an, das nicht in der Medikamentendatenbank enthalten ist.
                Es kann danach über die Suche gefunden werden."
          />
          <CustomDrugForm
              class="mt-5"
              :error="createCustomDrugError"
              @save="saveCustomDrug"
              @cancel="customDrugModalVisibility = false"
          />
        </UCard>
      </UModal>
    </div>
    <!-- TABLE -->
    <div class="flex flex-row justify-center max-w-6xl mx-auto">
      <div class="border-2 border-[#ededed] rounded-md shadow-lg">
        <h4 style="text-align: center; padding-top: 25px">Medikationen</h4>
        <div>
          <div class="flex px-3 py-3.5 border-b border-gray-200 dark:border-gray-700">
            <UInput v-model="q" placeholder="Tabelle Filtern" />
          </div>
          <UTable :rows="rows" :columns="columns" class="break-words">
            <template v-if="userStore.isAdmin" #actions-data="{ row }">
              <UDropdown :items="myOptions(row)">
                <UButton color="gray" variant="ghost" icon="i-heroicons-ellipsis-horizontal-20-solid" />
              </UDropdown>
            </template>
          </UTable>
          <div
            v-if="tableContent.length >= pageCount || filteredRows.length >= pageCount"
            class="flex justify-center px-3 py-3.5 border-t dark:border-red-500"
          >
            <UPagination
              v-model="page" :page-count="pageCount" :total="filteredRows.length" :ui="{
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
          <UButton
            label="Interview Beenden" color="green" variant="soft"
            class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" style="margin: 25px"
            @click="saveInterview()" />
        </div>
      </div>
    </div>

    <!-- MODALS -->
    
    <UModal v-model="deleteModalVisibility">
      <div class="p-4">
        <div style="text-align: center">
          <h4 style="color: red">Sie löschen folgenden Eintrag:</h4>
          <br>
          <h4>{{ drugToDelete.drug }}</h4>
          <br>
          <UForm :state="deleteState" class="space-y-4" @submit="deleteIntake">
            <UButton
              type="submit" color="red" variant="soft"
              class="border border-red-500 hover:bg-red-300 hover:border-white hover:text-white"
            >
              Eintrag löschen
            </UButton>
          </UForm>
        </div>
      </div>
    </UModal>
    <UModal v-model="editModalVisible">
      <div class="p-4">
        <div style="text-align: center">
          <div>
            <IntakeSearch
              @drug-selected="drugId => toEditDrug = drugId"
            />
            <IntakeForm
              :edit="true"
              :drug-id="toEditDrug"
              :initial-state="intakeToEdit"
              @save="saveEditIntake"
              @cancel="() => { editModalVisible = false }"
            />
          </div>
        </div>
      </div>
    </UModal>
    <UModal v-model="userStore.firstEvent" @close="resetFirstEvent()">
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

import type {DrugBody} from "~/components/CustomDrugForm.vue";
import type {IntakeFormSchema} from "~/components/IntakeForm/index.vue";
import dayjs from "dayjs";

const route = useRoute();
const router = useRouter();
const studyStore = useStudyStore();
const userStore = useUserStore();
const { $medlogapi } = useNuxtApp();

const createCustomDrugError = ref("");

const { data: latestItems, pending } = await useAsyncData(
  'latestItems',
  () => $medlogapi(
    `/api/study/{studyId}/proband/{probandId}/interview/last/intake`, {
      path: {
          studyId: route.params.study_id,
          probandId: route.params.proband_id,
        }
    }
  )
);

const drugForIntake = ref(undefined);

async function saveIntake(data: IntakeFormSchema) {
  const body = {
    administered_by_doctor: null, // TODO set dynamically
    as_needed_dose_unit: null,
    consumed_meds_today: data.medsTakenToday,
    dose_per_day: data.dose,
    drug_id: data.drugId,
    intake_end_time_utc: data.endTime ? dayjs(data.endTime).format("YYYY-MM-DD") : undefined,
    intake_regular_or_as_needed: data.frequency,
    intake_start_time_utc: data.startTime ? dayjs(data.startTime).format("YYYY-MM-DD") : undefined,
    regular_intervall_of_daily_dose: data.intervall,
    source_of_drug_information: data.drugSource
  };

  if (body.intake_regular_or_as_needed === 'as needed') {
    delete body.dose_per_day;
    delete body.regular_intervall_of_daily_dose;
  }

  const { error } = await useMedlogapi("/api/study/{study_id}/interview/{interview_id}/intake", {
    method: "POST",
    body: body,
    path: {
      study_id: route.params.study_id,
      interview_id: route.params.interview_id
    }
  });

  if (error.value) {
    console.error(error.value);
  }

  await loadIntakeList();
}

// Editform Modal

const editModalVisible = ref(false);
const toEditDrug = ref();
const intakeToEdit = ref<IntakeFormSchema>();
const intakeIdToEdit = ref();

const tableContent = ref([]);

async function openEditModal(row: object) {
  intakeIdToEdit.value = row.intakeId;
  const { data, error } = await useMedlogapi('/api/study/{study_id}/interview/{interview_id}/intake/{intake_id}', {
    method: "GET",
    path: {
      study_id: route.params.study_id,
      interview_id: route.params.interview_id,
      intake_id: intakeIdToEdit.value,
    }
  });

  if (error.value) {
    console.error(error.value);
    return;
  }

  intakeToEdit.value = {
    dose: data.value.dose_per_day,
    drugId: data.value.drug_id,
    drugSource: data.value.source_of_drug_information,
    endTime: data.value.intake_end_time_utc,
    frequency: data.value.intake_regular_or_as_needed,
    intervall: data.value.regular_intervall_of_daily_dose,
    medsTakenToday: data.value.consumed_meds_today,
    startTime: data.value.intake_start_time_utc,
  }

  toEditDrug.value = intakeToEdit.value.drugId;
  editModalVisible.value = true
}

async function saveEditIntake(data: IntakeFormSchema) {
  const body = {
    administered_by_doctor: null, // TODO set dynamically
    as_needed_dose_unit: null,
    consumed_meds_today: data.medsTakenToday,
    dose_per_day: data.dose,
    drug_id: data.drugId,
    intake_end_time_utc: data.endTime ? dayjs(data.endTime).format("YYYY-MM-DD") : undefined,
    intake_regular_or_as_needed: data.frequency,
    intake_start_time_utc: data.startTime ? dayjs(data.startTime).format("YYYY-MM-DD") : undefined,
    regular_intervall_of_daily_dose: data.intervall,
    source_of_drug_information: data.drugSource
  };

  if (body.intake_regular_or_as_needed === 'as needed') {
    delete body.dose_per_day;
    delete body.regular_intervall_of_daily_dose;
  }

  const { error } = await useMedlogapi('/api/study/{study_id}/interview/{interview_id}/intake/{intake_id}',
      {
        method: "PATCH",
        body: body,
        path: {
          study_id: route.params.study_id,
          interview_id: route.params.interview_id,
          intake_id: intakeIdToEdit.value,
        }
      }
  );

  if (error.value) {
    console.error(error.value);
    return;
  }

  editModalVisible.value = false;
  await loadIntakeList();
}

// Deleteform Modal

const deleteModalVisibility = ref(false);
const drugToDelete = ref();

const deleteState = reactive<{drug: string | undefined}>({
  drug: undefined,
});

async function openDeleteModal(row: object) {
  deleteState.drug = "";
  deleteModalVisibility.value = true;
  drugToDelete.value = row;
}

async function deleteIntake() {

  try {

    await $medlogapi(
      `/api/study/{studyId}/interview/{interviewId}/intake/{drugToDelete}`,
      {
        method: "DELETE",
        path: {
          studyId: route.params.study_id,
          interviewId: route.params.interview_id,
          drugToDelete: drugToDelete.value.intakeId
        }
      }
    );
    deleteModalVisibility.value = false;
    await loadIntakeList();
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
    key: "actions",
  },
];

const myOptions = (row) => [
  [
    {
      label: "Bearbeiten",
      icon: "i-heroicons-pencil-square-20-solid",
      click: () => openEditModal(row),
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

async function openCustomModal() {
  customDrugModalVisibility.value = true
}

async function saveCustomDrug(customDrugBody: DrugBody) {
  createCustomDrugError.value = "";
  const { error } = await useMedlogapi(
      `/api/drug/custom`,
      {
        method: "POST",
        body: customDrugBody
      }
  );

  if (error.value) {
    createCustomDrugError.value = error.value;
    return;
  }

  // TODO select newly created drug in the form

  customDrugModalVisibility.value = false;
}


// REST

async function saveInterview() {

  try {
    await $medlogapi(
      `/api/study/{studyId}/event/{eventId}/interview/{interviewId}`,
      {
        method: "PATCH",
        body: {
          "proband_external_id": `${route.params.proband_id}`,
          "interview_end_time_utc": new Date().toISOString(),
          "proband_has_taken_meds": true
        },
        path: {
          studyId: route.params.study_id,
          eventId: route.params.event_id,
          interviewId: route.params.interview_id
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

async function loadIntakeList() {
  try {
    const intakes = await $medlogapi(
      `/api/study/{studyId}/proband/{probandId}/intake/details?interview_id={interviewId}`,
    {
      path: {
        studyId: route.params.study_id,
        probandId: route.params.proband_id,
        interviewId: route.params.interview_id
        }
    });

    if (intakes && intakes.items) {
      tableContent.value = intakes.items.map((item) => ({
        pzn: item.drug.codes?.PZN,
        source: item.source_of_drug_information,
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

const resetFirstEvent = () => {
  userStore.firstEvent = false;
}

loadIntakeList();

</script>


<style scoped>
/* I don't like that this is here but I can't get the wordbreak otherwise */
:deep(td) {
  white-space: normal !important;
  word-break: break-word !important;
}
</style>

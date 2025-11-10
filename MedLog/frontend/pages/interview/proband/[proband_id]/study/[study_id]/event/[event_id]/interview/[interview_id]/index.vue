<template>
  <div class="mt-4 max-w-6xl mx-auto">
    <div v-if="loading">
      <UProgress animation="carousel" />
    </div>

    <UAlert v-else-if="errorMessage" color="red" title="Fehler" :description="errorMessage" />

    <div v-else class="flex flex-col self-center justify-center gap-4 mt-4 max-w-6xl mx-auto">
      <UCard>
        <div class="flex flex-row justify-between items-center space-x-4">
          <div class="w-1/4">
            <span class="text-lg">{{ studyStore.nameForStudy(studyId) || 'N/A' }}</span>
          </div>

          <div class="w-1/4 text-center">
            <span class="text-lg">{{ eventStore.nameForEvent(eventId) || 'N/A' }}</span>
          </div>

          <div class="w-1/4 text-center">
            <ULink :to="`/interview/proband/${probandId}/study/${studyId}`" inactive-class="text-red-800">
              <span class="text-lg">Proband <span class="font-mono">#{{ probandId || '???' }}</span></span>
            </ULink>
          </div>

          <div class="w-1/4 text-end">
          <span v-if="interview.interview_end_time_utc">
            Interview abgeschlossen am {{ formatDate(interview.interview_end_time_utc) }}
          </span>
            <UButton
                v-else
                label="Interview Beenden"
                color="red"
                variant="outline"
                icon="i-heroicons-arrow-right-on-rectangle"
                @click="endInterview()"
            />
          </div>
        </div>
      </UCard>

      <UCard :ui="{ body: { padding: 'py-4 sm:px-0' } }">
        <template #header>
          <div class="flex flex-col">
            <h2 class="text-lg self-center">Medikationen</h2>
            <div class="flex flex-row justify-between">
              <UInput v-model="q" placeholder="Tabelle Filtern" />
              <CopyPreviousDrugs
                  v-if="!pending && latestItems && interviewId !== latestItems[0]?.interview_id"
                  :on-update="loadIntakeList" />
              <UButton
                  class="self-end"
                  label="Präparat erfassen"
                  @click="openCreateIntakeModal"
              />
            </div>
          </div>
        </template>

        <div class="flex flex-col gap-4">
          <UTable :rows="rows" :columns="columns" class="break-words">
            <template v-if="userStore.isAdmin" #actions-data="{ row }">
              <UDropdown :items="myOptions(row)">
                <UButton color="gray" variant="ghost" icon="i-heroicons-ellipsis-horizontal-20-solid" />
              </UDropdown>
            </template>
          </UTable>

          <UPagination
              v-if="tableContent.length >= pageCount || filteredRows.length >= pageCount"
              v-model="page"
              :page-count="pageCount"
              :total="filteredRows.length"
              class="self-center"
          />
        </div>
      </UCard>

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
      <IntakeModal
          v-if="createIntakeModalVisible"
          v-model="createIntakeModalVisible"
          prevent-close
          @save="saveIntake"
          @cancel="() => { createIntakeModalVisible = false }"
      />
      <IntakeModal
          v-if="editModalVisible"
          v-model="editModalVisible"
          :initial-state="intakeToEdit"
          :is-drug-editable="false"
          prevent-close
          @save="saveEditIntake"
          @cancel="() => { editModalVisible = false }"
      />
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
    </div>
  </div>
</template>

<script setup lang="ts">
import type { IntakeFormSchema } from "~/components/Intake/Form.vue";
import dayjs from "dayjs";
import type { Interview } from "~/stores/interviewStore";

const route = useRoute();
const eventStore = useEventStore();
const studyStore = useStudyStore();
const userStore = useUserStore();
const { $medlogapi } = useNuxtApp();

const interviewId = computed(() => route.params.interview_id);
const probandId = computed(() => route.params.proband_id);
const studyId = computed(() => route.params.study_id);

const errorMessage = ref('');
const eventId = ref('');
const interview = ref<Interview | null>();
const loading = ref(true);

const { data: latestItems, pending } = await useAsyncData(
  'latestItems',
  () => $medlogapi(
    `/api/study/{studyId}/proband/{probandId}/interview/last/intake`, {
      path: {
          studyId: studyId.value,
          probandId: probandId.value,
        }
    }
  )
);

const createIntakeModalVisible = ref(false);

function openCreateIntakeModal() {
  createIntakeModalVisible.value = true;
}

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
      study_id: studyId.value,
      interview_id: interviewId.value
    }
  });

  if (error.value) {
    console.error(error.value);
    return;
  }

  createIntakeModalVisible.value = false;
  await loadIntakeList();
}

// Editform Modal

const editModalVisible = ref(false);
const intakeToEdit = ref<IntakeFormSchema>();
const intakeIdToEdit = ref();

const tableContent = ref([]);

async function openEditModal(row: object) {
  intakeIdToEdit.value = row.intakeId;
  const { data, error } = await useMedlogapi('/api/study/{study_id}/interview/{interview_id}/intake/{intake_id}', {
    method: "GET",
    path: {
      study_id: studyId.value,
      interview_id: interviewId.value,
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
          study_id: studyId.value,
          interview_id: interviewId.value,
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
          studyId: studyId.value,
          interviewId: interviewId.value,
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

// REST

async function endInterview() {
  await usePatchInterview(studyId.value, eventId.value, interviewId.value, {
    interview_end_time_utc: new Date().toISOString()
  });

  await navigateTo(`/interview/proband/${probandId.value}/study/${studyId.value}`);
}

async function loadIntakeList() {
  try {
    const intakes = await $medlogapi(
      `/api/study/{studyId}/proband/{probandId}/intake/details?interview_id={interviewId}`,
    {
      path: {
        studyId: studyId.value,
        probandId: probandId.value,
        interviewId: interviewId.value,
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

onMounted(async () => {
  loading.value = true;
  try {
    await eventStore.loadAllEventsForStudy(studyId.value);
    const interviewsForProband = await useGetInterviewsByStudyAndProband(studyId.value, probandId.value);
    const foundInterview = interviewsForProband.find(item => item.id === interviewId.value);
    console.log(foundInterview);
    if (!foundInterview) {
      errorMessage.value = 'Interview nicht gefunden';
      return;
    }
    eventId.value = foundInterview.event_id;
    interview.value = await useGetInterview(studyId.value, eventId.value, interviewId.value);
    console.log(interview.value);
    await loadIntakeList();
  } catch (error) {
    errorMessage.value = error.message ?? error;
  } finally {
    loading.value = false;
  }
})

</script>


<style scoped>
/* I don't like that this is here but I can't get the wordbreak otherwise */
:deep(td) {
  white-space: normal !important;
  word-break: break-word !important;
}
</style>

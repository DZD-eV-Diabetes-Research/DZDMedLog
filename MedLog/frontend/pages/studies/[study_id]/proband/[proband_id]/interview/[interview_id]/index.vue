<template>
  <div class="mt-4 max-w-6xl mx-auto">
    <div v-if="loading">
      <UProgress animation="carousel" />
    </div>

    <ErrorMessage v-else-if="error" :error="error" />

    <div v-else class="flex flex-col self-center justify-center gap-4 mt-4 max-w-6xl mx-auto">
      <UCard>
        <div class="flex flex-row justify-between items-start space-x-4 break-words">
          <div class="py-1.5" style="max-width: 25%">
            <span class="text-lg">{{ studyStore.nameForStudy(studyId) || 'N/A' }}</span>
          </div>

          <div class="py-1.5" style="max-width: 25%">
            <span class="text-lg">{{ eventStore.nameForEvent(eventId) || 'N/A' }}</span>
          </div>

          <div class="text-center" style="word-break: break-word; max-width: 25%">
            <UButton
                :to="`/studies/${studyId}/proband/${probandId}`"
                :label="`Proband #${probandId ?? '???'}`"
                class="text-lg"
                variant="link"
                icon="i-heroicons-arrow-right-circle"
                trailing
            />
          </div>

          <div class="py-1.5 text-end" style="max-width: 25%">
            <span v-if="interview?.interview_end_time_utc">
              Interview abgeschlossen am<br>
              <time :datetime="$dayjs.utc(interview.interview_end_time_utc).format()">
                {{ $dayjs.utc(interview.interview_end_time_utc).local().format('LLL') }}
              </time>
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

      <div class="grid grid-cols-2 gap-4">
        <UCard
          :class="{
            'bg-blue-100': drugsAvailableToCopy,
            'border-blue-400': drugsAvailableToCopy,
            'bg-gray-100': !drugsAvailableToCopy,
            'border-gray-400': !drugsAvailableToCopy,
          }"
          :ui="{
            header: {
              padding: 'pt-5 pb-2'
            },
            divide: '',
            body: {
              padding: 'py-4 sm:p-4 sm:px-6'
            },
          }"
        >
          <template #header>
            <h2 class="text-lg font-semibold">Medikamente übernehmen</h2>
          </template>

          <p v-if="!latestItems?.length">
            Es sind keine Medikamente aus einem früheren Interview verfügbar.
          </p>
          <p v-else-if="interview?.interview_end_time_utc">
            Keine Übernahme, da Interview bereits abgeschlossen ist.
          </p>
          <p v-else-if="!drugsAvailableToCopy">
            Medikamentenübernahme nicht verfügbar
          </p>
          <p v-else>
            Datenübernahme aus dem zuletzt geführten Interview
          </p>

          <div class="text-center mt-2">
            <CopyPreviousDrugs
                :deactivated="!drugsAvailableToCopy"
                :on-update="loadIntakeList"
            />
          </div>
        </UCard>
        <UCard
            class="bg-green-100 border-green-400 text-end"
            :ui="{
            header: {
              padding: 'pt-5 pb-2'
            },
            divide: '',
            body: {
              padding: 'py-4 sm:p-4 sm:px-6'
            },
          }"
        >
          <template #header>
            <h2 class="text-lg font-semibold">Einnahme erfassen</h2>
          </template>

          <p>
            Datenbankgestützte Erfassung von eingenommenen Medikamenten
          </p>
          <div class="text-center mt-2">
            <UButton
                class="justify-self-end"
                label="Medikament erfassen"
                icon="i-heroicons-plus"
                @click="openCreateIntakeModal"
            />
          </div>
        </UCard>
      </div>

      <UCard :ui="{ body: { padding: 'py-4 sm:px-0' } }">
        <template #header>
          <div class="flex flex-col">
            <h2 class="text-lg self-center">Eingenommene Medikamente</h2>
            <div class="inline-grid grid-cols-3 justify-items-center">
              <UInput v-model="q" placeholder="Tabelle filtern" autocomplete="off" class="justify-self-start" />
            </div>
          </div>
        </template>

        <div class="flex flex-col gap-4">
          <IntakeTable
              :intakes="rows"
              :can-edit="userStore.isAdmin"
              :can-delete="userStore.isAdmin"
              @edit="(intakeId: string) => openEditModal(intakeId)"
              @delete="(row: object) => openDeleteModal(row)"
          />

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

      <ConfirmationModal
          v-model="deleteModalVisibility"
          confirm-label="Eintrag löschen"
          :is-dangerous-to-confirm="true"
          @cancel="deleteModalVisibility = false"
          @confirm="deleteIntake"
      >
        <template #description>
          <p class="break-all">
            Möchten Sie den Eintrag für
            <span class="font-semibold">{{ drugToDelete?.name ?? 'N/A' }}</span>
            wirklich löschen?
          </p>
        </template>
      </ConfirmationModal>
      <IntakeModal
          v-if="createIntakeModalVisible"
          v-model="createIntakeModalVisible"
          :ui="{ width: 'w-full sm:max-w-3xl' }"
          prevent-close
          @save="saveIntake"
          @cancel="() => { createIntakeModalVisible = false }"
      />
      <IntakeModal
          v-if="editModalVisible"
          v-model="editModalVisible"
          :initial-state="intakeToEdit"
          :is-drug-editable="false"
          :ui="{ width: 'w-full sm:max-w-3xl' }"
          prevent-close
          @save="saveEditIntake"
          @cancel="() => { editModalVisible = false }"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useMedlogapi } from '#open-fetch'
import type { IntakeFormSchema } from "~/components/Intake/Form.vue";
import { useDayjs } from '#dayjs'
import localizedFormat from 'dayjs/plugin/localizedFormat'
import {
  computed,
  navigateTo,
  onMounted,
  ref,
  useAsyncData,
  useDeleteIntake,
  useEventStore,
  useGetIntake,
  useGetIntakesByStudyAndProband,
  useGetInterview,
  useGetInterviewsByStudyAndProband,
  useInterviewStore,
  useNuxtApp,
  useRoute,
  useStudyStore,
  useToast,
  useUserStore,
} from "#imports";
import type {SchemaIntakeCreateApi, SchemaIntakeDetailListItem, SchemaInterview} from "#open-fetch-schemas/medlogapi";

const route = useRoute();
const dayjs = useDayjs();
const eventStore = useEventStore();
const interviewStore = useInterviewStore();
const studyStore = useStudyStore();
const toast = useToast();
const userStore = useUserStore();
const { $medlogapi } = useNuxtApp();

dayjs.extend(localizedFormat);

const interviewId = computed(() => route.params.interview_id as string);
const probandId = computed(() => route.params.proband_id as string);
const studyId = computed(() => route.params.study_id as string);

const error = ref();
const eventId = ref('');
const interview = ref<SchemaInterview | null>();
const loading = ref(true);

const { data: latestItems, pending } = await useAsyncData(
  'latestItems',
  () => $medlogapi(
    '/api/study/{study_id}/proband/{proband_id}/interview/last/intake', {
      path: {
          study_id: studyId.value,
          proband_id: probandId.value,
        }
    }
  )
);

const drugsAvailableToCopy = computed(() => { return !pending.value && latestItems.value?.length && !loading.value && !interview.value?.interview_end_time_utc})

const createIntakeModalVisible = ref(false);

function openCreateIntakeModal() {
  createIntakeModalVisible.value = true;
}

async function saveIntake(data: IntakeFormSchema) {
  const body: SchemaIntakeCreateApi = {
    administered_by_doctor: data.administeredByDoctor,
    as_needed_dose_unit: null,
    consumed_meds_today: data.medsTakenToday,
    dose_per_day: data.dose,
    drug_id: data.drugId,
    intake_end_date: data.endDate ? dayjs(data.endDate).format("YYYY-MM-DD") : null,
    intake_end_date_option: data.endDateOption ?? null,
    intake_regular_or_as_needed: data.frequency,
    intake_start_date: data.startDate ? dayjs(data.startDate).format("YYYY-MM-DD") : null,
    intake_start_date_option: data.startDateOption ?? null,
    is_activeingredient_equivalent_choice: data.isActiveIngredientEquivalentChoice,
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
    toast.add({
      title: "Konnte Einnahme nicht anlegen",
      description: useGetErrorMessage(error),
    });
    return;
  }

  createIntakeModalVisible.value = false;
  await loadIntakeList();
}

// Editform Modal

const editModalVisible = ref(false);
const intakeToEdit = ref<Partial<IntakeFormSchema>>();
const intakeIdToEdit = ref();

const tableContent = ref<SchemaIntakeDetailListItem[]>([]);

async function openEditModal(intakeId: string) {
  intakeIdToEdit.value = intakeId;
  try {
    const intake = await useGetIntake(studyId.value, interviewId.value, intakeIdToEdit.value);

    intakeToEdit.value = {
      administeredByDoctor: intake.administered_by_doctor === null ? undefined : intake.administered_by_doctor,
      dose: intake.dose_per_day === null ? undefined : intake.dose_per_day,
      drugId: intake.drug_id ?? "",
      drugSource: intake.source_of_drug_information === null ? undefined : intake.source_of_drug_information,
      endDate: intake.intake_end_date ?? undefined,
      endDateOption: intake.intake_end_date_option ?? undefined,
      frequency: intake.intake_regular_or_as_needed === null ? undefined : intake.intake_regular_or_as_needed,
      intervall: intake.regular_intervall_of_daily_dose === null ? undefined : intake.regular_intervall_of_daily_dose,
      isActiveIngredientEquivalentChoice: intake.is_activeingredient_equivalent_choice,
      medsTakenToday: intake.consumed_meds_today,
      startDate: intake.intake_start_date ?? undefined,
      startDateOption: intake.intake_start_date_option ?? undefined,
    }
  } catch (error) {
    toast.add({
      title: "Konnte Einnahme nicht abrufen",
      description: useGetErrorMessage(error),
    });
    return;
  }

  editModalVisible.value = true
}

async function saveEditIntake(data: IntakeFormSchema) {
  const body = {
    administered_by_doctor: data.administeredByDoctor,
    as_needed_dose_unit: null,
    consumed_meds_today: data.medsTakenToday,
    dose_per_day: data.dose,
    drug_id: data.drugId,
    intake_end_date: data.endDate ? dayjs(data.endDate).format("YYYY-MM-DD") : null,
    intake_end_date_option: data.endDateOption ?? null,
    intake_regular_or_as_needed: data.frequency,
    intake_start_date: data.startDate ? dayjs(data.startDate).format("YYYY-MM-DD") : null,
    intake_start_date_option: data.startDateOption ?? null,
    is_activeingredient_equivalent_choice: data.isActiveIngredientEquivalentChoice,
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
    toast.add({
      title: "Konnte Einnahme nicht speichern",
      description: useGetErrorMessage(error),
    });
    return;
  }

  editModalVisible.value = false;
  await loadIntakeList();
}

// Deleteform Modal

const deleteModalVisibility = ref(false);
const drugToDelete = ref();

async function openDeleteModal(row: object) {
  deleteModalVisibility.value = true;
  drugToDelete.value = row;
}

async function deleteIntake() {
  try {
    await useDeleteIntake(studyId.value, interviewId.value, drugToDelete.value.intakeId)
    deleteModalVisibility.value = false;
    await loadIntakeList();
  } catch (error) {
    toast.add({
      title: "Konnte Einnahme nicht löschen",
      description: useGetErrorMessage(error),
    });
  }
}

// Table

const page = ref(1);
const pageCount = 10;

const rows = computed(() => {
  const data = q.value ? filteredRows.value : tableContent.value;
  return data.slice((page.value - 1) * pageCount, page.value * pageCount);
});

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
  await interviewStore.endInterview(studyId.value, eventId.value, interviewId.value);
  await navigateTo(`/studies/${studyId.value}/proband/${probandId.value}`);
}

async function loadIntakeList() {
  try {
    tableContent.value = await useGetIntakesByStudyAndProband(studyId.value, probandId.value, interviewId.value) ?? [];
  } catch (e) {
    error.value = new Error("Konnte Liste der Einnahmen nicht laden", { cause: e });
  }
}

onMounted(async () => {
  loading.value = true;
  try {
    await eventStore.loadAllEventsForStudy(studyId.value);
    const interviewsForProband = await useGetInterviewsByStudyAndProband(studyId.value, probandId.value);
    const foundInterview = interviewsForProband.find(item => item.id === interviewId.value);
    if (!foundInterview) {
      error.value = new Error('Interview nicht gefunden');
      return;
    }
    eventId.value = foundInterview.event_id;
    interview.value = await useGetInterview(studyId.value, eventId.value, interviewId.value);
    await loadIntakeList();
  } catch (e) {
    error.value = e;
  } finally {
    loading.value = false;
  }
})

</script>


<style scoped>

</style>

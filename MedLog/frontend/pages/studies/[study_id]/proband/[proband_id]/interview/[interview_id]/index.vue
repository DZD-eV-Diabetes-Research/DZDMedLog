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

      <UCard :ui="{ body: { padding: 'py-4 sm:px-0' } }">
        <template #header>
          <div class="flex flex-col">
            <h2 class="text-lg self-center">Medikationen</h2>
            <div class="flex flex-row justify-between">
              <UInput v-model="q" placeholder="Tabelle filtern" autocomplete="off" />
              <CopyPreviousDrugs
                  v-if="!pending && latestItems?.length && !interview.interview_end_time_utc"
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
import type { SchemaInterview } from "#open-fetch-schemas/medlogapi";

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
    administered_by_doctor: data.administeredByDoctor,
    as_needed_dose_unit: null,
    consumed_meds_today: data.medsTakenToday,
    dose_per_day: data.dose,
    drug_id: data.drugId,
    intake_end_time_utc: data.endTime ? dayjs(data.endTime).format("YYYY-MM-DD") : null,
    intake_regular_or_as_needed: data.frequency,
    intake_start_time_utc: data.startTime ? dayjs(data.startTime).format("YYYY-MM-DD") : null,
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
      description: error.value.data?.detail ?? error.message ?? error,
    });
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

async function openEditModal(intakeId: string) {
  intakeIdToEdit.value = intakeId;
  try {
    const intake = await useGetIntake(studyId.value, interviewId.value, intakeIdToEdit.value);

    intakeToEdit.value = {
      administeredByDoctor: intake.administered_by_doctor,
      dose: intake.dose_per_day,
      drugId: intake.drug_id,
      drugSource: intake.source_of_drug_information,
      endTime: intake.intake_end_time_utc,
      frequency: intake.intake_regular_or_as_needed,
      intervall: intake.regular_intervall_of_daily_dose,
      isActiveIngredientEquivalentChoice: intake.is_activeingredient_equivalent_choice,
      medsTakenToday: intake.consumed_meds_today,
      startTime: intake.intake_start_time_utc,
    }
  } catch (error) {
    toast.add({
      title: "Konnte Einnahme nicht abrufen",
      description: error.value.data?.detail ?? error.message ?? error,
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
    intake_end_time_utc: data.endTime ? dayjs(data.endTime).format("YYYY-MM-DD") : null,
    intake_regular_or_as_needed: data.frequency,
    intake_start_time_utc: data.startTime ? dayjs(data.startTime).format("YYYY-MM-DD") : null,
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
      description: error.value.data?.detail ?? error.message ?? error,
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
      description: error.message ?? error,
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

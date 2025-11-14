<template>
  <section class="container w-11/12 lg:w-8/12 xl:w-6/12 mx-auto mt-8">
    <h1 class="text-4xl font-normal text-center mb-4">Proband #{{ probandId }}</h1>

    <div v-if="loading">
      <UProgress animation="carousel" />
    </div>

    <UAlert v-else-if="errorMessage" color="red" title="Fehler" :description="errorMessage" />

    <div v-else class="flex flex-col self-center justify-center gap-4 mt-4 max-w-6xl mx-auto">
      <UAlert
          v-if="currentInterview"
          color="amber"
          title="Laufendes Interview"
          :description="`Das Interview für Event '${ eventStore.nameForEvent(currentInterview.event_id) }' wurde noch nicht abgeschlossen.`"
          :actions="[
            {
              label: 'Interview abschließen',
              variant: 'outline',
              color: 'gray',
              click: () => endInterview(currentInterview.event_id, currentInterview.id),
            },
            {
              label: 'Interview fortsetzen',
              variant: 'outline',
              color: 'gray',
              click: () => navigateTo(`/studies/${studyId}/proband/${probandId}/interview/${currentInterview.id}`),
            },
        ]"
      />

      <UCard>
        <div class="flex flex-row justify-between items-center space-x-4">
          <div class="w-1/2 flex flex-col gap-4 items-center">
            <span>Letztes abgeschlossenes Interview</span>
            <div v-if="lastInterview" class="text-center">
              <UButton
                  :to="`/studies/${studyId}/proband/${probandId}/interview/${lastInterview.id}`"
                  :label="eventStore.nameForEvent(lastInterview.event_id)"
                  class="text-lg"
                  variant="link"
                  icon="i-heroicons-arrow-right-circle"
                  trailing
              />
              <br>
              <span class="text-base">
                {{ formatDate(lastInterview.interview_start_time_utc) }}
              </span>
            </div>
            <span v-else class="text-lg">
              Keines
            </span>
          </div>

          <div class="w-1/2 flex flex-col gap-4 items-center">
            <span>Interview starten</span>
            <div class="flex flex-row gap-2">
              <UInputMenu v-model="eventToStart" :options="eventsToStartOptions" />
              <UButton color="green" :disabled="!eventToStart" @click="introModalVisible = true">
                Interview starten
              </UButton>
            </div>
          </div>
        </div>
      </UCard>

      <UAccordion
        v-if="completedInterviews.length"
        :items="[{
          label: `Abgeschlossene Interviews (${completedInterviews.length})`,
          icon: 'i-heroicons-clipboard-document-check',
          slot: 'past-interviews',
        }]"
        color="emerald"
        variant="solid"
      >
        <template #past-interviews>
          <InterviewTable :interviews="completedInterviews" :study-id="studyId" class="" />
        </template>
      </UAccordion>

      <UCard :ui="{ body: { padding: 'py-4 sm:px-0' } }">
        <template #header>
          <div class="flex flex-col">
            <h2 class="text-lg self-center">Medikationshistorie</h2>
            <div class="flex flex-row justify-between">
              <UInput v-model="tableFilterString" placeholder="Tabelle filtern" />
            </div>
          </div>
        </template>

        <div class="flex flex-col gap-4">
          <IntakeTable :intakes="rows" :show-event="true" />

          <UPagination
              v-if="intakes.length >= itemsPerPage || filteredRows.length >= itemsPerPage"
              v-model="page"
              :page-count="itemsPerPage"
              :total="filteredRows.length"
              class="self-center"
          />
        </div>
      </UCard>
    </div>
    <InterviewIntroModal v-model="introModalVisible" @start="startInterview" @cancel="introModalVisible = false" />
  </section>
</template>

<script setup lang="ts">
import type { Events } from "~/stores/eventStore";
import type { Interview } from "~/stores/interviewStore";

const route = useRoute()
const eventStore = useEventStore()
const interviewStore = useInterviewStore()

const currentInterview = ref<Interview>();
const errorMessage = ref('');
const eventsForProband = ref<Events>([]);
const eventToStart = ref();
const interviewsForProband = ref<Interview[]>([]);
const introModalVisible = ref(false);
const lastInterview = ref<Interview>();
const loading = ref(true);

const probandId = computed(() => route.params.proband_id);
const studyId = computed(() => route.params.study_id);
const eventsToStartOptions = computed(() => {
  const untouchedEvents = eventsForProband.value.filter(item => item.proband_interview_count === 0);;
  return untouchedEvents.map(event => ({
    id: event.id,
    event: event,
    label: event.name,
    order: event.order_position
  })).sort((a, b) => a.order - b.order)
});
const completedInterviews = computed(() => {
  return interviewsForProband.value.filter(interview => interview.interview_end_time_utc !== null);
});

// table

const page = ref(1)
const itemsPerPage = 10
const intakes = ref([])
const tableFilterString = ref('')

const rows = computed(() => {
  const data = tableFilterString.value ? filteredRows.value : intakes.value;
  return data.slice((page.value - 1) * itemsPerPage, page.value * itemsPerPage);
})

const filteredRows = computed(() => {
  if (!tableFilterString.value) {
    return intakes.value
  }

  return intakes.value.filter((tableContent) => {
    return Object.values(tableContent).some((value) => {
      return String(value).toLowerCase().includes(tableFilterString.value.toLowerCase())
    })
  })
})

async function startInterview(hasTakenMeds: boolean) {
  try {
    const interview = await useCreateInterview(studyId.value, eventToStart.value.id, probandId.value, hasTakenMeds)

    await navigateTo(`/studies/${studyId.value}/proband/${probandId.value}/interview/${interview.id}`)
  }
  catch (error) {
    console.log(error);
  }
}

async function endInterview(eventId, interviewId) {
  try {
    loading.value = true;
    await interviewStore.endInterview(studyId.value, eventId, interviewId);
    interviewsForProband.value = await useGetInterviewsByStudyAndProband(studyId.value, probandId.value);
    currentInterview.value = await useGetCurrentInterviewByStudyAndProband(studyId.value, probandId.value);
    lastInterview.value = await useGetLastInterviewByStudyAndProband(studyId.value, probandId.value);
  } catch (error) {
    console.log(error);
    errorMessage.value = error.message ?? error;
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  try {
    loading.value = true;
    await eventStore.loadAllEventsForStudy(studyId.value);
    eventsForProband.value = await useGetEventsByStudyAndProband(studyId.value, probandId.value);
    interviewsForProband.value = await useGetInterviewsByStudyAndProband(studyId.value, probandId.value);
    currentInterview.value = await useGetCurrentInterviewByStudyAndProband(studyId.value, probandId.value);
    lastInterview.value = await useGetLastInterviewByStudyAndProband(studyId.value, probandId.value);
    intakes.value = await useGetIntakesByStudyAndProband(studyId.value, probandId.value) ?? [];
  } catch (error) {
    errorMessage.value = error.message ?? error;
  } finally {
    loading.value = false;
  }
})

</script>

<style scoped>

</style>

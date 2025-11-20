<template>
  <section class="container w-11/12 lg:w-8/12 xl:w-6/12 mx-auto mt-8">
    <h1 class="text-4xl font-normal text-center mb-4">Proband #{{ probandId }}</h1>

    <div v-if="loading">
      <UProgress animation="carousel" />
    </div>

    <UAlert v-else-if="errorMessage" color="red" title="Fehler" :description="errorMessage" />

    <div v-else class="flex flex-col self-center justify-center gap-4 mt-4 max-w-6xl mx-auto">
      <UCard>
        <div class="flex flex-row justify-between items-start space-x-4">
          <div class="w-1/2 flex flex-col gap-4 items-center">
            <span class="font-semibold">Letztes abgeschlossenes Interview</span>
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
            <span class="font-semibold">Interview starten</span>
            <UAlert
                v-if="currentInterview"
                title="Laufendes Interview"
                color="orange"
                variant="subtle"
                :description="`Das Interview für Event '${ eventStore.nameForEvent(currentInterview.event_id) }' wurde noch nicht abgeschlossen.`"
                :ui="{ actions: 'flex flex-row justify-between mt-4' }"
            >
              <template #description>
                Das Interview für das Event <span class="font-semibold font-mono">{{ eventStore.nameForEvent(currentInterview.event_id) || 'N/A' }}</span> wurde noch nicht abgeschlossen.
                Vor dem Start eines neuen Interviews muss das laufende Interview beendet sein.
              </template>
              <template #actions>
                <UButton
                    label="Interview abschließen"
                    variant="outline"
                    color="red"
                    icon="i-heroicons-stop-solid"
                    @click="endInterview(currentInterview.event_id, currentInterview.id)"
                />
                <UButton
                    label="Interview fortsetzen"
                    icon="i-heroicons-arrow-right-circle"
                    trailing
                    :to="`/studies/${studyId}/proband/${probandId}/interview/${currentInterview.id}`"
                />
              </template>
            </UAlert>
            <div v-else-if="eventsToStartOptions.length" class="flex flex-row gap-2">
              <USelect v-model="eventIdToStart" :options="eventsToStartOptions" />
              <UButton color="green" :disabled="!eventIdToStart" @click="introModalVisible = true">
                Interview starten
              </UButton>
            </div>
            <UAlert
                v-else
                description="Alle Events wurden bereits bearbeitet, daher kann kein neues Interview gestartet werden."
                color="orange"
                variant="outline"
            />
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
const eventIdToStart = ref();
const eventsToStartOptions = ref<{ label: string; value: string }[]>([]);
const interviewsForProband = ref<Interview[]>([]);
const introModalVisible = ref(false);
const lastInterview = ref<Interview>();
const loading = ref(true);

const probandId = computed(() => route.params.proband_id);
const studyId = computed(() => route.params.study_id);
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
    const interview = await useCreateInterview(studyId.value, eventIdToStart.value, probandId.value, hasTakenMeds)

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

function fillInterviewStartSelector() {
  const untouchedEvents = eventsForProband.value.filter(item => item.proband_interview_count === 0);
  const sortedEvents = untouchedEvents.sort((a, b) => a.order_position - b.order_position);
  eventsToStartOptions.value = sortedEvents.map(event => ({
    value: event.id,
    label: event.name,
  }));

  if (eventsToStartOptions.value.length > 0) {
    eventIdToStart.value = eventsToStartOptions.value[0].value;
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

    fillInterviewStartSelector();
  } catch (error) {
    errorMessage.value = error.message ?? error;
  } finally {
    loading.value = false;
  }
})

</script>

<style scoped>

</style>

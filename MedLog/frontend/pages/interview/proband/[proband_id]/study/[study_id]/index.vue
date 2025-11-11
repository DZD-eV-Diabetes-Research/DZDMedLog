<template>
  <div>
    <div class="flex flex-row gap-4 justify-center max-w-6xl m-auto">
      <div class="w-[50%]">
        <UIBaseCard>
          <h5>Unbearbeitete Events</h5>
          <UInputMenu v-model="selectedIncompleteEvent" :options="incompletedItems" />
          <br>
          <div class="flex justify-evenly">
            <UButton
              color="green"
              variant="soft"
              class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white"
              @click="createInterview()"
            >
              Interview Durchführen
            </UButton>
          </div>
        </UIBaseCard>
      </div>
      <div class="w-[50%]">
        <UIBaseCard>
          <h5>Bearbeitete Events</h5>
          <UInputMenu v-model="selectedCompleteEvent" :options="completedItems" />
          <br>
          <UButton
            color="blue" variant="soft"
            class="border border-blue-500 hover:bg-blue-300 hover:border-white hover:text-white"
            @click="editEvent(selectedCompleteEvent.id)"
          >
            Interview Bearbeiten
          </UButton>
        </UIBaseCard>
      </div>
    </div>
    <UModal v-model="showEventModal">
      <div class="p-4" style="text-align: center">
        <UForm :schema="eventSchema" :state="eventState" class="space-y-4" @submit="createEvent">
          <UFormGroup label="Event Name" name="name">
            <UInput v-model="eventState.name" required placeholder="Interview Campaign Year Quarter" />
          </UFormGroup>
          <h3 v-if="eventError" style="color: red;">{{ eventError }}</h3>
          <UButton
            type="submit" label="Event anlegen" color="green" variant="soft"
            class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
        </UForm>
      </div>
    </UModal>
    <br>
    <div class="flex flex-row justify-center max-w-8xl mx-auto">
      <div class="border-2 border-[#ededed] rounded-md shadow-lg">
      <h4 style="text-align: center; padding-top: 25px;">Medikationshistorie</h4>
      <div>
        <div class="flex px-3 py-3.5 border-b border-gray-200 dark:border-gray-700">
          <UInput v-model="q" placeholder="Tabelle Filtern" />
        </div>
        <IntakeTable :intakes="rows" :show-event="true" />
        <div
          v-if="intakes.length >= pageCount || filteredRows.length >= pageCount"
          class="flex justify-center px-3 py-3.5 border-t dark:border-green-700"
        >
          <UPagination
            v-model="page" :page-count="pageCount" :total="filteredRows.length" :ui="{
              wrapper: 'flex items-center gap-1',
              rounded: 'rounded-sm',
              default: {
                activeButton: {
                  variant: 'outline',
                }
              }
            }" />
        </div>
      </div>
    </div>
    </div>
    <div style="text-align:center; margin-top:2%" />
  </div>
</template>

<script setup lang="ts">

import { object, string } from "yup";
import { useMedlogapi } from '#open-fetch';

// general constants
const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const { $medlogapi } = useNuxtApp();

const probandId = computed(() => route.params.proband_id);
const studyId = computed(() => route.params.study_id);

// table

const page = ref(1)
const pageCount = 10

const intakes = ref([])

const rows = computed(() => {
  const data = q.value ? filteredRows.value : intakes.value;
  return data.slice((page.value - 1) * pageCount, page.value * pageCount);
})

const q = ref('')

const filteredRows = computed(() => {
  if (!q.value) {
    return intakes.value
  }

  return intakes.value.filter((tableContent) => {
    return Object.values(tableContent).some((value) => {
      return String(value).toLowerCase().includes(q.value.toLowerCase())
    })
  })
})

// Completed Events

const selectedCompleteEvent = ref()
const completedItems = ref([]);

// Create new events

const showEventModal = ref(false)
const eventState = reactive({ name: "" });
const eventSchema = object({
  name: string().required("Required"),
});
const eventError = ref("")

async function createEvent() {
  try {
    await useCreateEvent(eventState.name.trim(), studyId.value);

    const events = await $medlogapi('/api/study/{studyId}/proband/{probandId}/event',
      {
        path: {
          studyId: studyId.value,
          probandId: probandId.value
        }
      }
    )
    incompletedItems.value = events.items.filter(item => item.proband_interview_count === 0);
    incompletedItems.value = incompletedItems.value.map(event => ({
      id: event.id,
      event: event,
      label: event.name
    }))
    selectedIncompleteEvent.value = incompletedItems.value[0];
    showEventModal.value = !showEventModal.value
  } catch (error) {
    eventError.value = error.response._data.detail
    console.error("Failed to create event: ", error.response._data.detail);
  }
}

async function createInterview() {
  try {
    const interview = await useCreateInterview(studyId.value, selectedIncompleteEvent.value.id, probandId.value, true, userStore.userID)
    userStore.firstEvent = true;
    router.push("/interview/proband/" + probandId.value + "/study/" + studyId.value + "/event/" + selectedIncompleteEvent.value.id + "/interview/" + interview.id)
  }
  catch (error) {
    console.log(error);
  }
}

// Incompleted Events

const selectedIncompleteEvent = ref()
const incompletedItems = ref([]);

// REST 

const { data: events } = await useMedlogapi('/api/study/{studyId}/proband/{probandId}/event', {
  path: {
    studyId: studyId.value,
    probandId: probandId.value,
  }
})

function createEventList(events) {
  if (events && events.items) {
    completedItems.value = events.items.filter(item => item.proband_interview_count > 0);
    completedItems.value = completedItems.value.map(event => ({
      id: event.id,
      event: event,
      label: event.name,
      order: event.order_position
    })).sort((a, b) => b.order - a.order)

    incompletedItems.value = events.items.filter(item => item.proband_interview_count === 0);
    incompletedItems.value = incompletedItems.value.map(event => ({
      id: event.id,
      event: event,
      label: event.name,
      order: event.order_position
    })).sort((a, b) => a.order - b.order)
  }

  selectedCompleteEvent.value = completedItems.value[0]
  selectedIncompleteEvent.value = incompletedItems.value[0]
}

watch(events, (newEvents) => {
  if (newEvents) {
    createEventList(newEvents)
  }
}, { immediate: true })

async function editEvent(eventId: string) {
  const { data: result, error } = await useMedlogapi('/api/study/{study_id}/event/{event_id}/interview', {
    path: {
      study_id: studyId.value,
      event_id: eventId,      }
  })

  if (error.value) {
    console.error(error);
    return;
  }

  const interview = result.value.find(item => item.proband_external_id == probandId.value);

  await navigateTo(`/interview/proband/${probandId.value}/study/${studyId.value}/event/${eventId}/interview/${interview.id}`);
}

async function createIntakeList() {
  try {
    intakes.value = await useGetIntakesByStudyAndProband(studyId.value, probandId.value) ?? [];
  } catch (error) {
    console.log(error);
  }
}

createIntakeList()

</script>

<style scoped>

</style>

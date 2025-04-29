<template>
  <Layout>
    <div class="flex flex-row gap-4">
      <div class="flex flex-1">
        <UIBaseCard class="w-full">
          <h5>Unbearbeitete Events</h5>
          <UInputMenu v-model="selectedIncompleteEvent" :options="incompletedItems" />
          <br>
          <div class="flex justify-evenly">
            <UButton @click="createInterview()" color="green" variant="soft"
              class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white">
              Interview Durchführen
            </UButton>
            <UButton v-if="userStore.isAdmin" @click="openEventModal()" color="green" variant="soft"
              class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white">
              Neues Event anlegen
            </UButton>
          </div>
        </UIBaseCard>
      </div>
      <div class="flex flex-1">
        <UIBaseCard class="w-full">
          <h5>Bearbeitete Events</h5>
          <UInputMenu v-model="selectedCompleteEvent" :options="completedItems" />
          <br>
          <UButton @click="editEvent(selectedCompleteEvent.id)" color="blue" variant="soft"
            class="border border-blue-500 hover:bg-blue-300 hover:border-white hover:text-white">
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
          <UButton type="submit" label="Event anlegen" color="green" variant="soft"
            class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
        </UForm>
      </div>
    </UModal>
    <br>
    <div class="border-2 border-[#ededed] rounded-md shadow-lg">
      <h4 style="text-align: center; padding-top: 25px;">Medikationshistorie</h4>
      <div>
        <div class="flex px-3 py-3.5 border-b border-gray-200 dark:border-gray-700">
          <UInput v-model="q" placeholder="Tabelle Filtern" />
        </div>
        <UTable :rows="rows" :columns="columns">
        </UTable>
        <div v-if="tableContent.length >= pageCount || filteredRows.length >= pageCount" class="flex justify-center px-3 py-3.5 border-t 
        dark:border-green-700">
          <UPagination v-model="page" :page-count="pageCount" :total="filteredRows.length" :ui="{
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
    <div style="text-align:center; margin-top:2%">
    </div>
  </Layout>
</template>

<script setup lang="ts">

import { object, number, date, string, type InferType } from "yup";

// general constants
const route = useRoute()
const router = useRouter()
const runtimeConfig = useRuntimeConfig()
const tokenStore = useTokenStore()
const userStore = useUserStore()
const studyStore = useStudyStore()
const { $api } = useNuxtApp();

// table

const page = ref(1)
const pageCount = 10

const tableContent = ref([])

const rows = computed(() => {
  const data = q.value ? filteredRows.value : tableContent.value;
  return data.slice((page.value - 1) * pageCount, page.value * pageCount);
})

const columns = [{
  key: 'event',
  label: 'Event',
  sortable: true
}, {
  key: "pzn",
  label: "PZN",
},
{
  key: "custom",
  label: "Custom"
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
}]


const q = ref('')

const filteredRows = computed(() => {
  if (!q.value) {
    return tableContent.value
  }

  return tableContent.value.filter((tableContent) => {
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
    await useCreateEvent(eventState.name.trim(), route.params.study_id);

    const events = await $api(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/proband/${route.params.proband_id}/event`)
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
    const interview = await useCreateInterview(route.params.study_id, selectedIncompleteEvent.value.id, route.params.proband_id, true, userStore.userID)
    studyStore.event = selectedIncompleteEvent.value.event.name
    userStore.firstEvent = true;
    router.push("/interview/proband/" + route.params.proband_id + "/study/" + route.params.study_id + "/event/" + selectedIncompleteEvent.value.id + "/interview/" + interview.id)
  }
  catch (error) {
    console.log(error);
  }
}

// Incompleted Events

const selectedIncompleteEvent = ref()
const incompletedItems = ref([]);

// REST 

const { data: events } = await useAPI(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/proband/${route.params.proband_id}/event`)

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
  try {
    const result = await $api(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/event/${eventId}/interview`)

    studyStore.event = selectedCompleteEvent.value.event.name
    router.push("/interview/proband/" + route.params.proband_id + "/study/" + route.params.study_id + "/event/" + eventId + "/interview/" + result[0].id)
  } catch (error) {
    console.log(error);
  }
}

async function createIntakeList() {
  try {
    const intakes = await $api(
      `${runtimeConfig.public.baseURL}study/${route.params.study_id}/proband/${route.params.proband_id}/intake/details`);

    if (intakes && intakes.items) {
      tableContent.value = intakes.items.map((item) => ({
        event: item.event.name,
        pzn: item.drug.codes.PZN,
        source: useDrugSourceTranslator(item.source_of_drug_information, null),
        drug: item.drug.trade_name,
        intervall: useIntervallDoseTranslator(item.regular_intervall_of_daily_dose, null),
        dose: item.dose_per_day === 0 ? "/" : item.dose_per_day,
        time: item.intake_end_time_utc === null ? item.intake_start_time_utc + " bis unbekannt" : item.intake_start_time_utc + " bis " + item.intake_end_time_utc,
        darr: item.drug.attrs_ref.darreichungsform.display + " (" + item.drug.attrs_ref.darreichungsform.value + ")",
        id: item.id ? item.id : item.custom_drug_id,
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

//eventmodal logic

const openEventModal = () => {
  showEventModal.value = true;
  eventError.value = "";
}

createIntakeList()

</script>

<style scoped>
:deep(td) {
  white-space: normal !important;
  word-break: break-word !important;
}
</style>

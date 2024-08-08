<template>
  <Layout>
    <div class="card-container">
      <UIBaseCard>
        <h5>Unbearbeitete Events</h5>
        <UInputMenu v-model="selectedIncompleteEvent" :options="incompletedItems" />
        <br>
        <div class="button-container">
          <UButton @click="createInterview()" color="green" variant="soft"
            class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white">
            Interview Durchführen
          </UButton>
          <UButton v-if="userStore.isAdmin" @click="showEventModal = !showEventModal" color="green" variant="soft"
            class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white">
            Neues Event anlegen
          </UButton>
        </div>
      </UIBaseCard>
      <UIBaseCard>
        <h5>Bearbeitete Events</h5>
        <UInputMenu v-model="selectedCompleteEvent" :options="completedItems" />
        <br>
        <UButton @click="editEvent(selectedCompleteEvent.id)" color="blue" variant="soft"
          class="border border-blue-500 hover:bg-blue-300 hover:border-white hover:text-white">
          Interview Bearbeiten
        </UButton>
      </UIBaseCard>
    </div>
    <UModal v-model="showEventModal">
      <div class="p-4" style="text-align: center">
        <UForm :schema="eventSchema" :state="eventState" class="space-y-4" @submit="createEvent">
          <UFormGroup label="Event Name" name="name">
            <UInput v-model="eventState.name" required placeholder="Interview Campaign Year Quarter" />
          </UFormGroup>
          <UButton type="submit" label="Event anlegen" color="green" variant="soft"
            class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
        </UForm>
      </div>
    </UModal>
    <br>
    <div class="tableDiv">
      <h4 style="text-align: center; padding-top: 25px;">Medikationshistorie</h4>
      <div>
        <div class="flex px-3 py-3.5 border-b border-gray-200 dark:border-gray-700">
          <UInput v-model="q" placeholder="Tabelle Filtern" />
        </div>
        <UTable :rows="rows" :columns="columns">
        </UTable>
        <div v-if="tableContent.length >= pageCount || filteredRows.length >= pageCount" class="flex justify-center px-3 py-3.5 border-t 
        dark:border-green-700 dark:border-red-500">
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
    <UButton @click="getDownload" color="green" variant="soft" 
    class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white">Download</UButton>
    </div>
    <a href="http://localhost:8888/study/b2afcc3c-0877-4000-acc6-82eec4955327/export/fea3c12b-f498-4f0d-9f2d-f8b8f60f8390/download">download</a>

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

// table

const page = ref(1)
const pageCount = 15

const tableContent = ref([])

const rows = computed(() => {
  const data = q.value ? filteredRows.value : tableContent.value;
  return data.slice((page.value - 1) * pageCount, page.value * pageCount);
})

const columns = [{
  key: 'event',
  label: 'Event',
  sortable: true
},{
    key: "pzn",
    label: "PZN",
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

async function createEvent() {
  try {
    await useCreateEvent(eventState.name.trim(), route.params.study_id);

    const events = await $fetch(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/proband/${route.params.proband_id}/event`, {
      method: "GET",
      headers: { 'Authorization': "Bearer " + tokenStore.access_token },
    })
    incompletedItems.value = events.items.filter(item => item.proband_interview_count === 0);
    incompletedItems.value = incompletedItems.value.map(event => ({
      id: event.id,
      event: event,
      label: event.name
    }))
    selectedIncompleteEvent.value = incompletedItems.value[0];
    showEventModal.value = !showEventModal.value
  } catch (error) {
    console.error("Failed to create event: ", error);
  }
}

async function createInterview() {
  try {
    const interview = await useCreateInterview(route.params.study_id, selectedIncompleteEvent.value.id, route.params.proband_id, true, userStore.userID)
    studyStore.event = selectedIncompleteEvent.value.event.name
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

const { data: events } = await useFetch(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/proband/${route.params.proband_id}/event`, {
  method: "GET",
  headers: { 'Authorization': "Bearer " + tokenStore.access_token },
})

function createEventList(events) {
  if (events && events.items) {
    completedItems.value = events.items.filter(item => item.proband_interview_count > 0);
    completedItems.value = completedItems.value.map(event => ({
      id: event.id,
      event: event,
      label: event.name,
      order: event.order_position
    })).sort((a,b) => b.order - a.order)

    incompletedItems.value = events.items.filter(item => item.proband_interview_count === 0);
    incompletedItems.value = incompletedItems.value.map(event => ({
      id: event.id,
      event: event,
      label: event.name,
      order: event.order_position
    })).sort((a,b) => a.order - b.order)
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
    const result = await $fetch(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/event/${eventId}/interview`, {
      method: "GET",
      headers: { 'Authorization': "Bearer " + tokenStore.access_token },
    })
    studyStore.event = selectedCompleteEvent.value.event.name
    router.push("/interview/proband/" + route.params.proband_id + "/study/" + route.params.study_id + "/event/" + eventId + "/interview/" + result[0].id)
  } catch (error) {
    console.log(error);
  }
}

async function createIntakeList() {
  try {
    const intakes = await $fetch(
      `${runtimeConfig.public.baseURL}study/${route.params.study_id}/proband/${route.params.proband_id}/intake/details`,
      {
        method: "GET",
        headers: { Authorization: "Bearer " + tokenStore.access_token },
      }
    );

    if (intakes && intakes.items) {
      tableContent.value = intakes.items.map((item) => ({
        event: item.event.name,
        pzn: item.pharmazentralnummer,
        source: useDrugSourceTranslator(item.source_of_drug_information, null),
        drug: item.drug.name,
        intervall: useIntervallDoseTranslator(item.regular_intervall_of_daily_dose,null),
        dose: item.dose_per_day === 0 ? "" : item.dose_per_day,
        time: item.intake_end_time_utc === null ? item.intake_start_time_utc + " bis unbekannt" : item.intake_start_time_utc + " bis " + item.intake_end_time_utc,
        darr: item.drug.darrform_ref.bedeutung + " (" + item.drug.darrform_ref.darrform + ")",
        id: item.id ? item.id : item.custom_drug_id,
        custom: item.custom_drug_id ? true : false,
        class: item.custom_drug_id
          ? "bg-yellow-500/50 dark:bg-yellow-400/50"
          : null,
      }));
    }
  } catch (error) {
    console.log(error);
  }
}

// async function getDownload() {
//   const response = await fetch('http://localhost:8888/study/b2afcc3c-0877-4000-acc6-82eec4955327/export/fea3c12b-f498-4f0d-9f2d-f8b8f60f8390/download', {
//     method: "GET",
//     headers: {
//     'Authorization': "Bearer " + tokenStore.access_token, 
//     'Accept': '*/*',
//     },
//   });

//   if (response.ok) {
//     const blob = await response.blob();
//     const url = window.URL.createObjectURL(blob);
//     const a = document.createElement('a');
//     a.href = url;
//     a.download = 'your_file.csv';
//     document.body.appendChild(a);
//     a.click();
//     a.remove();
//     window.URL.revokeObjectURL(url);
//   } else {
//     console.error('Failed to download file:', response.statusText);
//   }
// }

async function getDownload() {
  const fileUrl = 'http://localhost:8888/study/b2afcc3c-0877-4000-acc6-82eec4955327/export/fea3c12b-f498-4f0d-9f2d-f8b8f60f8390/download';
  
  try {
    const response = await fetch(fileUrl, {
      method: "GET",
      headers: {
        'Authorization': "Bearer " + tokenStore.access_token,
        'Accept': '*/*',
      },
    });

    if (response.ok) {
      const a = document.createElement('a');
      a.href = fileUrl;
      a.download = 'your_file.csv';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } else {
      console.error('Failed to download file:', response.statusText);
    }
  } catch (error) {
    console.error('Failed to download file:', error.message);
  }
}



createIntakeList()

</script>

<style scoped>
.card-container {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.card-container>* {
  flex: 1;
}

.button-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 0 1rem;
  gap: 1rem;
}

.tableDiv {
  border-radius: 10px;
  border-width: 2px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.26);
}
</style>

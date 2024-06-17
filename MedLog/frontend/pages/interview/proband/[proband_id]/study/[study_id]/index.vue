<template>
  <Layout>
    {{ route.params }}
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
    <div>
      <div class="flex px-3 py-3.5 border-b border-gray-200 dark:border-gray-700">
        <UInput v-model="q" placeholder="Filter people..." />
      </div>

      <UTable :rows="filteredRows" :columns="columns" />
    </div>
    {{ intakes.items }}
  </Layout>
</template>

<script setup lang="ts">

const columns = [{
  key: 'id',
  label: 'ID'
}, {
  key: 'name',
  label: 'Name'
}, {
  key: 'title',
  label: 'Title'
}, {
  key: 'email',
  label: 'Email'
}, {
  key: 'role',
  label: 'Role'
}]

const people = [{
  id: 1,
  name: 'Lindsay Walton',
  title: 'Front-end Developer',
  email: 'lindsay.walton@example.com',
  role: 'Member'
}, {
  id: 2,
  name: 'Courtney Henry',
  title: 'Designer',
  email: 'courtney.henry@example.com',
  role: 'Admin'
}, {
  id: 3,
  name: 'Tom Cook',
  title: 'Director of Product',
  email: 'tom.cook@example.com',
  role: 'Member'
}, {
  id: 4,
  name: 'Whitney Francis',
  title: 'Copywriter',
  email: 'whitney.francis@example.com',
  role: 'Admin'
}, {
  id: 5,
  name: 'Leonard Krasner',
  title: 'Senior Designer',
  email: 'leonard.krasner@example.com',
  role: 'Owner'
}, {
  id: 6,
  name: 'Floyd Miles',
  title: 'Principal Designer',
  email: 'floyd.miles@example.com',
  role: 'Member'
}]

const q = ref('')

const filteredRows = computed(() => {
  if (!q.value) {
    return people
  }

  return people.filter((person) => {
    return Object.values(person).some((value) => {
      return String(value).toLowerCase().includes(q.value.toLowerCase())
    })
  })
})

import { object, number, date, string, type InferType } from "yup";

const route = useRoute()
const router = useRouter()
const runtimeConfig = useRuntimeConfig()
const tokenStore = useTokenStore()
const userStore = useUserStore()
const studyStore = useStudyStore()

const { data: events } = await useFetch(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/proband/${route.params.proband_id}/event`, {
  method: "GET",
  headers: { 'Authorization': "Bearer " + tokenStore.access_token },
})

const { data: intakes } = await useFetch(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/proband/${route.params.proband_id}/intake`, {
  method: "GET",
  headers: { 'Authorization': "Bearer " + tokenStore.access_token },
})

const showEventModal = ref(false)
const selectedCompleteEvent = ref()
const selectedIncompleteEvent = ref()
const completedItems = ref([]);
const incompletedItems = ref([]);

const eventState = reactive({ name: "" });
const eventSchema = object({
  name: string().required("Required"),
});


function createEventList(events) {
  if (events && events.items) {
    completedItems.value = events.items.filter(item => item.proband_interview_count > 0);
    completedItems.value = completedItems.value.map(event => ({
      id: event.id,
      event: event,
      label: event.name
    })).sort().reverse()

    incompletedItems.value = events.items.filter(item => item.proband_interview_count === 0);
    incompletedItems.value = incompletedItems.value.map(event => ({
      id: event.id,
      event: event,
      label: event.name
    })).sort().reverse()
  }

  selectedCompleteEvent.value = completedItems.value[0]
  selectedIncompleteEvent.value = incompletedItems.value[0]
}

watch(events, (newEvents) => {
  if (newEvents) {
    createEventList(newEvents)
  }
}, { immediate: true })


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
    })).sort().reverse()
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

async function editEvent(eventId: string) {
  try {
    const result = await $fetch(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/event/${eventId}/interview`, {
      method: "GET",
      headers: { 'Authorization': "Bearer " + tokenStore.access_token },
    })
    router.push("/interview/proband/" + route.params.proband_id + "/study/" + route.params.study_id + "/event/" + eventId + "/interview/" + result[0].id)
  } catch (error) {
    console.log(error);
  }
}

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
</style>

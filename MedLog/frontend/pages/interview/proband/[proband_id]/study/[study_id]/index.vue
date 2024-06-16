<template>
  <Layout>
    Route params
    <br>
    {{ route.params }}
    <div class="card-container">
      <UIBaseCard>
        <h5>Zukünftige Interviews</h5>
        <UInputMenu v-model="selectedIncompleteEvent" :options="incompletedItems" />
        <br>
        <UButton @click="showInterviewModal = !showInterviewModal" color="green" variant="soft"
          class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white">
          Interview Durchführen
        </UButton>
      </UIBaseCard>
      <UIBaseCard>
        <h5>Durchgeführte Interviews</h5>
        <UInputMenu v-model="selectedCompleteEvent" :options="completedItems" />
        <br>
        <UButton @click="test2(selectedCompleteEvent)" color="blue" variant="soft"
          class="border border-blue-500 hover:bg-blue-300 hover:border-white hover:text-white">
          Interview Bearbeiten
        </UButton>
      </UIBaseCard>
    </div>
    <UModal v-model="showInterviewModal">
      <div class="p-4" style="text-align: center">
        <UForm :schema="interviewSchema" :state="interviewState" class="space-y-4" @submit="test">
          <h5>Interview anlegen für:</h5>
          <h5>{{ selectedIncompleteEvent.label }}</h5>
          <UFormGroup label="Probanden-ID" name="subjectID">
            <UInput v-model="interviewState.subjectID" required />
          </UFormGroup>
        </UForm>

        <!-- <UForm :schema="interviewSchema" :state="interviewState" class="space-y-4" @submit="createInterview()">
                    <h5>Interview anlegen für:</h5>
                    <h5>{{selectedStudy.display_name}}</h5>
                    <UFormGroup label="Probanden-ID" name="subjectID">
                        <UInput v-model="interviewState.subjectID" required />
                    </UFormGroup>
                    <UFormGroup label="Interview-Nummer" name="interviewNumber">
                        <UInput v-model="interviewState.interviewNumber" type="number" required />
                    </UFormGroup>
                    <URadioGroup v-model="selected" style="border: 'border border-black'"
                        legend="Haben Sie Diabetes-Medikamente in den vergangenen 12 Monaten bzw. andere Medikamente in den letzten 7 Tagen eingenommen?"
                        :options="options" />
                    <UInputMenu v-model="selectedEvent" :options="studyEvents" />
                    <UAccordion :items="accordionItems">
                        <template #create-event>
                            <UForm :schema="eventSchema" :state="eventState" class="space-y-4" @submit="createEvent">
                                <UFormGroup label="Event Name" name="name">
                                    <UInput v-model="eventState.name" required
                                        placeholder="Interview Campaign Year Quarter" />
                                </UFormGroup>
                                <UButton type="submit" label="Event anlegen" color="green" variant="soft"
                                    class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
                            </UForm>
                        </template>
</UAccordion>
<UButton type="submit" label="Interview anlegen" color="green" variant="soft"
  class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
</UForm> -->
      </div>
    </UModal>
    {{ selectedIncompleteEvent }}
  </Layout>
</template>

<script setup lang="ts">

const interviewState = reactive({
  subjectID: "",
  interviewNumber: null
});

const interviewSchema = object({
  subjectID: string().required("Required"),
  interviewNumber: number().required("Required")
});

const showForm = ref(false)

import dayjs from 'dayjs';
import { watchEffect } from 'vue';
import type { FormSubmitEvent } from "#ui/types";
import { object, number, date, string, type InferType } from "yup";


const route = useRoute()
const runtimeConfig = useRuntimeConfig()
const tokenStore = useTokenStore()
const drugStore = useDrugStore()
const studyStore = useStudyStore()
const probandStore = useProbandStore()

const { data: events } = await useFetch(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/event`, {
  method: "GET",
  headers: { 'Authorization': "Bearer " + tokenStore.access_token },
})

const showInterviewModal = ref(false)
const selectedCompleteEvent = ref()
const selectedIncompleteEvent = ref()
const completedItems = ref([]);
const incompletedItems = ref([]);

const { data: intake, refresh } = await useFetch(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/event`, {
  method: "GET",
  headers: { 'Authorization': "Bearer " + tokenStore.access_token },
})

function createEventList(events) {
  if (events && events.items) {
    completedItems.value = events.items.filter(item => item.completed);
    completedItems.value = completedItems.value.map(event => ({
      id: event.id,
      event: event,
      label: event.name
    })).sort((a, b) => a.label.localeCompare(b.label)).reverse()

    incompletedItems.value = events.items.filter(item => !item.completed);
    incompletedItems.value = incompletedItems.value.map(event => ({
      id: event.id,
      event: event,
      label: event.name
    })).sort((a, b) => a.label.localeCompare(b.label)).reverse()
  }

  selectedCompleteEvent.value = completedItems.value[0]
  selectedIncompleteEvent.value = incompletedItems.value[0]
}

watch(events, (newEvents) => {
  if (newEvents) {
    createEventList(newEvents)
  }
}, { immediate: true })

async function test(event: FormSubmitEvent<Schema>) {
  // Do something with event.data
  console.log(event.data)
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
</style>

<!-- 
<template>
    <Layout>
        <div class="center">
            <h1>Interviews</h1>
        </div>
        <UIBaseCard v-if="!studyStore.studies">
            <h2 v-if="userStore.isAdmin">Aktuell sind keine Studien aufgelistet bitte, legen Sie eine Studie an</h2>
            <h2 v-if="!userStore.isAdmin">Aktuell sind keine Studien aufgelistet bitte, wenden Sie sich an einen Admin
            </h2>
        </UIBaseCard>
        <UIBaseCard class="active" @click="selectStudy(study)" v-for="study in studyStore.studies.items" :key="study.id"
            style="text-align: center">
            <h3>{{ study.display_name }}</h3>
        </UIBaseCard>
        <UModal v-model="showInterviewModal">
            <div class="p-4" style="text-align: center">
                <UForm :schema="interviewSchema" :state="interviewState" class="space-y-4" @submit="createInterview()">
                    <h5>Interview anlegen für:</h5>
                    <h5>{{selectedStudy.display_name}}</h5>
                    <UFormGroup label="Probanden-ID" name="subjectID">
                        <UInput v-model="interviewState.subjectID" required />
                    </UFormGroup>
                    <UFormGroup label="Interview-Nummer" name="interviewNumber">
                        <UInput v-model="interviewState.interviewNumber" type="number" required />
                    </UFormGroup>
                    <URadioGroup v-model="selected" style="border: 'border border-black'"
                        legend="Haben Sie Diabetes-Medikamente in den vergangenen 12 Monaten bzw. andere Medikamente in den letzten 7 Tagen eingenommen?"
                        :options="options" />
                    <UInputMenu v-model="selectedEvent" :options="studyEvents" />
                    <UAccordion :items="accordionItems">
                        <template #create-event>
                            <UForm :schema="eventSchema" :state="eventState" class="space-y-4" @submit="createEvent">
                                <UFormGroup label="Event Name" name="name">
                                    <UInput v-model="eventState.name" required
                                        placeholder="Interview Campaign Year Quarter" />
                                </UFormGroup>
                                <UButton type="submit" label="Event anlegen" color="green" variant="soft"
                                    class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
                            </UForm>
                        </template>
</UAccordion>
<UButton type="submit" label="Interview anlegen" color="green" variant="soft"
    class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
</UForm>
</div>
</UModal>
    </Layout>
</template>

<script setup lang="ts">
import { object, string, type InferType, number } from 'yup'
import type { FormSubmitEvent } from '#ui/types'
import { async } from '../../../../../../composables/useCreateIntake';
import { useStudyStore } from '../../../../../../stores/studyStore';
import { useProbandStore } from '../../../../../../stores/probandStore';
import { UForm, UButton } from '../../../../../../.nuxt/components';
import { type } from '../../../../../../.nuxt/types/imports';

const schema = object({
    probandID: string().required('Required'),
})

type Schema = InferType<typeof schema>

const state = reactive({
    probandID: undefined,
})

async function test(event: FormSubmitEvent<Schema>) {
    console.log(event.data);
    
}

async function onSubmit (event: FormSubmitEvent<Schema>) {
  // Do something with event.data
  console.log(event.data)
}

const userStore = useUserStore()
const studyStore = useStudyStore()
const tokenStore = useTokenStore()
const router = useRouter()
const route = useRoute()
const runtimeConfig = useRuntimeConfig()

const showInterviewModal = ref(false)
const studyEvents = ref([]);
const selectedStudy = ref()
const selectedEvent = ref()

const toggleAccordion = ref(true)

const interviewState = reactive({
    subjectID: "",
    interviewNumber: null
});

const options = [{
    value: "false",
    label: "Nein"
}, {
    value: "true",
    label: "Ja"
}]

const selected = ref("true")

const interviewSchema = object({
    subjectID: string().required("Required"),
    interviewNumber: number().required("Required")
});

const accordionItems = [{
    label: 'Create Event',
    icon: 'i-heroicons-information-circle',
    slot: 'create-event',
}]

async function selectStudy(study) {
    try {
        const events = await $fetch(`${runtimeConfig.public.baseURL}study/${study.id}/event`, {
            method: "GET",
            headers: { 'Authorization': "Bearer " + tokenStore.access_token },
        })
        selectedStudy.value = study
        showInterviewModal.value = true
        studyEvents.value = events.items.map(event => ({ id: event.id, event: event, label: useStringDoc(event.name) }));
        studyEvents.value = studyEvents.value.slice().sort((a, b) => a.label.localeCompare(b.label)).reverse();
        selectedEvent.value = studyEvents.value[0]

    } catch (error) {
        console.log(error);
    }
}

async function createInterview() {
    let takenMeds = selected.value === "true"

    try {
        showInterviewModal.value = false;
        const responseData = await useCreateInterview(selectedStudy.value.id, selectedEvent.value.id, interviewState.subjectID, takenMeds, interviewState.interviewNumber);
        studyStore.event = selectedEvent.value.event.name
        router.push({ path: "/interview/" + selectedStudy.value.id + '/event/' + selectedEvent.value.id + "/id/" + responseData.id })
    } catch (error) {
        console.error("Failed to create Interview: ", error);
    }
}

const eventState = reactive({ name: "" });
const eventSchema = object({
    name: string().required("Required"),
});

async function createEvent() {
    try {
        await useCreateEvent(eventState.name.trim(), selectedStudy.value.id);

        const events = await $fetch(`${runtimeConfig.public.baseURL}study/${selectedStudy.value.id}/event`, {
            method: "GET",
            headers: { 'Authorization': "Bearer " + tokenStore.access_token },
        })
        studyEvents.value = events.items.map(event => ({ id: event.id, event: event, label: useStringDoc(event.name) }));
        studyEvents.value = studyEvents.value.slice().sort((a, b) => a.label.localeCompare(b.label)).reverse();
        selectedEvent.value = studyEvents.value[0];
    } catch (error) {
        console.error("Failed to create event: ", error);
    }
}

</script>

<style lang="scss" scoped>
.center {
    text-align: center;
    margin: auto;
    width: 50%;
    padding: 10px;
}
</style> -->
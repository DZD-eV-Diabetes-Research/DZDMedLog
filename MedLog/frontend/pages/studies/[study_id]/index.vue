<template>
  <section class="container w-11/12 lg:w-8/12 xl:w-6/12 mx-auto mt-8">
    <div class="flex justify-center break-all">
      <h3 class="text-4xl font-medium my-4">{{ study.display_name }}</h3>
    </div>
    <Draggable
      :list="myEvents" :disabled="!enabled" item-key="name" class="list-group" ghost-class="ghost"
      @start="dragging = true" @end="dragging = false"
    >
      <template #item="{ element }">
        <div class="list-group-item" :class="{ 'not-draggable': !enabled }">
          <UIBaseCard class="events" :class="{ sorted: isSorted }">{{
            element.name
            }}</UIBaseCard>
        </div>
      </template>
    </Draggable>
    <UIBaseCard v-if="myEvents.length === 0">
      <h5>Keine Events in der Studie aufgezeichnet</h5>
    </UIBaseCard>
    <UIBaseCard v-if="userStore.isAdmin" class="noHover" :naked="true">
      <div class="flex justify-center space-x-5 mx-auto">
        <UButton
          label="Event anlegen" color="green" variant="soft"
          class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white"
          @click="openEventModal()" />
        <UButton
          :label="sortButton"
          color="blue" variant="soft" class="border border-blue-500 hover:bg-blue-300 hover:border-white hover:text-white"
          @click="toggleSort()" />
      </div>
      <UModal v-model="showEventModal">
        <div class="p-4">
          <UForm :schema="eventSchema" :state="eventState" class="space-y-4" @submit="createEvent">
            <h3>Event anlegen</h3>
            <ErrorMessage v-if="createEventError" :error="createEventError" />
            <UFormGroup label="Event Name" name="name">
              <UInput v-model="eventState.name" required placeholder="Interview Nr. 1" />
            </UFormGroup>
            <UButton
              type="submit" label="Event anlegen" color="green" variant="soft"
              class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
          </UForm>
        </div>
      </UModal>
      
    </UIBaseCard>
  </section>
</template>

<script setup lang="ts">

import {  object, string } from "yup";

const enabled = ref(false);
const dragging = ref(false);
const { $medlogapi } = useNuxtApp();


const studyStore = useStudyStore();
const userStore = useUserStore();
const route = useRoute();

const createEventError = ref();
const isSorted = ref(false);
const sortButton = ref("Events Sortieren");

const showEventModal = ref(false);
const study = studyStore.getStudy(route.params.study_id);

const myEvents = ref([])

async function getEvents() {
  const events = await $medlogapi(
    `/api/study/{studyId}/event?hide_completed=false&offset=0&limit=100`, {
      path: {
        studyId: route.params.study_id
      }
    });
  myEvents.value = events.items
}

getEvents()

const eventState = reactive({ name: "" });

const eventSchema = object({
  name: string().required("Required"),
});

const test = ref([]);

async function toggleSort() {
  if (sortButton.value === "Sortierung Speichern") {
    sortButton.value = "Events Sortieren";

    myEvents.value.map((element) => {
      test.value.push(element);
    });
    await $medlogapi(
      `/api/study/{studyId}/event/order`,
      {
        method: "POST",
        body: test.value,
        path: {
          studyId: route.params.study_id
        }
      }
    );
  } else {
    sortButton.value = "Sortierung Speichern";
  }
  isSorted.value = !isSorted.value;
  enabled.value = !enabled.value;
}

async function openEventModal() {
  showEventModal.value = true;
  eventState.name = "";
  createEventError.value = undefined;
}

async function createEvent() {
  const body = { name: eventState.name };
  try {
    await $medlogapi(`/api/study/{studyId}/event`,
      {
        method: "POST",
        body,
        path: {
          studyId: route.params.study_id
        }
      }
    );
    showEventModal.value = false;
    await getEvents()
  } catch (error) {
    createEventError.value = error;
  }
}
</script>

<style scoped>
.events {
  text-align: center;
  margin: 1rem auto;
  max-width: 40rem;
  padding: 1rem;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.26);
}

.sorted {
  cursor: move;
  background-color: #d1e8ff;
}
</style>

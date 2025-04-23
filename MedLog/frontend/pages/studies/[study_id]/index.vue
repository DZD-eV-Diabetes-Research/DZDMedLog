<template>
  <Layout>
    <div class="center">
      <h3 class="text-4xl font-medium my-4">{{ study.display_name }}</h3>
    </div>
    <Draggable :list="myEvents" :disabled="!enabled" item-key="name" class="list-group" ghost-class="ghost"
      @start="dragging = true" @end="dragging = false">
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
        <UButton @click="openEventModal()" label="Event anlegen" color="green" variant="soft"
          class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
        <UButton @click="toggleSort()" :label="sortButton" color="blue" variant="soft"
          class="border border-blue-500 hover:bg-blue-300 hover:border-white hover:text-white" />
      </div>
      <UModal v-model="showEventModal">
        <div class="p-4" style="text-align: center">
          <UForm :schema="eventSchema" :state="eventState" class="space-y-4" @submit="createEvent">
            <h3>Event anlegen</h3>
            <h3 v-if="errorMessage" style="color: red">{{ errorMessage }}</h3>
            <UFormGroup label="Event Name" name="name">
              <UInput v-model="eventState.name" required placeholder="Interview Nr. 1" />
            </UFormGroup>
            <UButton type="submit" label="Event anlegen" color="green" variant="soft"
              class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
          </UForm>
        </div>
      </UModal>
      
    </UIBaseCard>
  </Layout>
</template>

<script setup lang="ts">

import { boolean, number, object, string, type InferType } from "yup";
import { computed } from "vue";

const enabled = ref(false);
const dragging = ref(false);
const { $api } = useNuxtApp();


const studyStore = useStudyStore();
const tokenStore = useTokenStore();
const userStore = useUserStore();
const runtimeConfig = useRuntimeConfig();
const route = useRoute();

const isSorted = ref(false);
const sortButton = ref("Events Sortieren");

const showEventModal = ref(false);
const study = await studyStore.getStudy(route.params.study_id);

const myEvents = ref([])

async function getEvents() {
  const events = await $api(
    `${runtimeConfig.public.baseURL}study/${route.params.study_id}/event?hide_completed=false&offset=0&limit=100`);
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
    await $api(
      `${runtimeConfig.public.baseURL}study/${route.params.study_id}/event/order`,
      {
        method: "POST",
        body: test.value,
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
  errorMessage.value = "";
}

const errorMessage = ref();

async function createEvent() {
  const body = { name: eventState.name };
  try {
    await $api(
      runtimeConfig.public.baseURL +
      "study/" +
      route.params.study_id +
      "/event",
      {
        method: "POST",
        body,
      }
    );
    showEventModal.value = false;
    // refresh()
    getEvents()
  } catch (error) {    
    errorMessage.value = error.response._data.detail;
    console.error("Failed to create event: ", error.response._data.detail);
  }
}
</script>

<style scoped>
.center {
  text-align: center;
  margin: auto;
  width: 50%;
  padding: 10px;
}

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
  background-color: #cee4fc;
}

.button-wrapper {
  display: flex;
  justify-content: center;
  width: 100%;
  margin-bottom: 1%;
}

.button-container {
  display: flex;
  gap: 20px;
}

.button-container UButton {
  flex: 0 1 auto; 
}

</style>

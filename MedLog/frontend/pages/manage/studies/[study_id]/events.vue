<template>
  <section v-if="userStore.isAdmin" class="container w-11/12 lg:w-8/12 xl:w-6/12 mx-auto mt-8">
    <div class="flex justify-center break-all mb-4 relative items-center">
      <div class="absolute left-0">
        <UButton
            to="/manage/studies"
            label="Zurück"
            title="Zur Studienverwaltung"
            variant="outline"
            color="gray"
            icon="i-heroicons-arrow-left-circle"
        />
      </div>
      <h1 class="text-4xl font-normal text-center">
        Events für {{ studyStore.nameForStudy(studyId) }}
      </h1>
    </div>

    <p class="my-4 text-center text-gray-500">
      Events bilden Termine wie Visiten oder Interviews ab.
    </p>

    <UProgress v-if="loading" animation="carousel" />
    <div v-else class="w-3/6 mx-auto">
      <div v-if="myEvents.length === 0">
        <UAlert
            description="Für diese Studie wurden noch keine Events konfiguriert."
            color="orange"
            variant="outline"
        />
      </div>
      <div v-else class="flex flex-col text-lg">
        <div class="flex flex-row justify-end">
          <UButton
              v-if="sortingMode"
              label="Abbrechen"
              variant="outline"
              color="gray"
              class="mr-4"
              @click="cancelReordering"
          />
          <UButton
              v-if="sortingMode"
              label="Reihenfolge speichern"
              @click="endReordering"
          />
          <UButton
              v-if="!sortingMode"
              label="Reihenfolge ändern"
              icon="i-heroicons-arrows-up-down"
              color="gray"
              variant="outline"
              @click="beginReordering"
          />
        </div>

        <Draggable
            :list="myEvents"
            :disabled="!sortingMode"
            item-key="name"
            ghost-class="ghost"
        >
          <template #item="{ element }">
            <div class="flex flex-row items-center justify-between border-b-2 border-b-slate-200 py-2">
              <span>{{ element.name }}</span>
              <UIcon v-show="sortingMode" name="i-heroicons-bars-3" class="ml-2 text-2xl text-gray-400 cursor-n-resize" />
            </div>
          </template>
        </Draggable>
      </div>

      <div class="mt-4 text-center">
        <UButton
            label="Event anlegen"
            icon="i-heroicons-plus"
            :disabled="sortingMode"
            @click="openEventModal()"
        />
      </div>
    </div>

    <UModal v-model="showCreateEventModal" prevent-close>
      <div class="p-4">
        <UForm :schema="eventSchema" :state="eventState" class="space-y-4" @submit="createEvent">
          <h3>Event anlegen</h3>
          <ErrorMessage v-if="createEventError" :error="createEventError" />
          <UFormGroup label="Name des Events" description="Der Name muss innerhalb der Studie eindeutig sein." name="name">
            <UInput v-model="eventState.name" required placeholder="Interview Nr. 1" />
          </UFormGroup>
          <hr>
          <div class="flex justify-between">
            <UButton label="Abbrechen" variant="outline" color="gray" @click.prevent="showCreateEventModal = false" />
            <UButton type="submit" label="Event anlegen" />
          </div>
        </UForm>
      </div>
    </UModal>
  </section>
  <section v-else class="container w-11/12 lg:w-8/12 xl:w-6/12 mx-auto mt-8">
    <ErrorMessage
        title="Keine Berechtigung"
        message="Ihnen fehlt die Berechtigung für diese Seite"
    />
  </section>
</template>

<script setup lang="ts">
import { object, string } from "yup";

const eventStore = useEventStore();
const studyStore = useStudyStore();
const toast = useToast();
const userStore = useUserStore();
const route = useRoute();

const createEventError = ref();
const loading = ref(false);
const showCreateEventModal = ref(false);
const sortingMode = ref(false);

const studyId = computed(() => {
  return route.params.study_id;
});

const myEvents = ref([])

async function loadEvents() {
  loading.value = true;
  myEvents.value = await useGetEventsByStudy(studyId.value);
  loading.value = false;
}

const eventState = reactive({ name: "" });

const eventSchema = object({
  name: string().required("Das Event muss einen Namen haben"),
});

function beginReordering() {
  sortingMode.value = true;
}

function cancelReordering() {
  sortingMode.value = false;
  loadEvents();
}

async function endReordering() {
  try {
    await useCreateEventOrder(studyId.value, myEvents.value.map(event => event.id));
    await loadEvents();
    await eventStore.loadAllEventsForStudy(studyId.value);
    sortingMode.value = false;
  } catch (error) {
    toast.add({
      title: "Konnte Reihenfolge nicht speichern",
      description: error.data?.detail ?? error.message ?? error,
    });
  }
}

async function openEventModal() {
  showCreateEventModal.value = true;
  eventState.name = "";
  createEventError.value = undefined;
}

async function createEvent() {
  try {
    await useCreateEvent(eventState.name, studyId.value);
    showCreateEventModal.value = false;
    await loadEvents()
    await eventStore.loadAllEventsForStudy(studyId.value);
  } catch (error) {
    createEventError.value = error;
  }
}

onMounted(() => {
  loadEvents();
});
</script>

<style scoped>

</style>

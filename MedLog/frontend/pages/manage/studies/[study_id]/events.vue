<template>
  <section v-if="studyPermissionStore.currentUserCanManageStudy(studyId)" class="container w-11/12 lg:w-8/12 xl:w-6/12 mx-auto mt-8">
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
      <h1 class="text-4xl font-normal text-center w-8/12">
        Events für {{ studyStore.nameForStudy(studyId) }}
      </h1>
    </div>

    <p class="my-4 text-center text-gray-500">
      Events bilden Termine wie Visiten oder Interviews ab.
    </p>

    <UAlert
        v-if="!studyIsActive"
        class="mb-4"
        icon="i-heroicons-archive-box"
        color="orange"
        variant="outline"
        title="Studie ist deaktiviert"
        description="Die Events einer deaktivierten Studie können nicht geändert werden. Reaktivieren Sie die Studie, um Events anzulegen, umzubenennen oder umzusortieren."
    />

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
        <div v-if="studyIsActive" class="flex flex-row justify-end">
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
          <template #item="{ element }: { element: SchemaEvent }">
            <div class="flex flex-row items-center justify-between border-b-2 border-b-slate-200 py-2">
              <div class="flex flex-row flex-wrap items-center gap-2">
                <span>{{ element.name }}</span>
                <UBadge v-if="element.external_id" color="gray" variant="subtle" size="xs" class="text-gray-700" title="Externe ID">
                  ID: {{ element.external_id }}
                </UBadge>
                <UBadge v-if="eventTypeBadgeLabel(element)" color="primary" variant="subtle" size="xs" class="text-primary-700" title="Art des Interviews">
                  {{ eventTypeBadgeLabel(element) }}
                </UBadge>
              </div>
              <div>
                <UIcon v-show="sortingMode" name="i-heroicons-bars-3" class="ml-2 text-2xl text-gray-400 cursor-n-resize" />
                <UButton
                    v-show="!sortingMode"
                    title="Event bearbeiten ..."
                    variant="outline"
                    color="gray"
                    icon="i-heroicons-pencil"
                    class="ml-2"
                    @click="openEditEventModal(element)"
                />
                <UButton
                    v-show="!sortingMode"
                    title="Event löschen ..."
                    variant="outline"
                    color="red"
                    icon="i-heroicons-trash"
                    class="ml-2"
                    @click="deleteEvent(element)"
                />
              </div>
            </div>
          </template>
        </Draggable>
      </div>

      <div v-if="studyIsActive" class="mt-4 text-center">
        <UButton
            label="Event anlegen"
            icon="i-heroicons-plus"
            :disabled="sortingMode"
            @click="openCreateEventModal()"
        />
      </div>
    </div>

    <DZDUIModal v-model="showCreateEventModal" title="Event anlegen" :error="createEventError">
      <EventForm :submit-callback="createEvent" @cancel="showCreateEventModal = false" />
    </DZDUIModal>
    <DZDUIModal v-model="showEditEventModal" title="Event bearbeiten" :error="editEventError">
      <EventForm :initial-state="eventFormInitialState" :submit-callback="updateEvent" @cancel="showEditEventModal = false" />
    </DZDUIModal>
  </section>
  <section v-else class="container w-11/12 lg:w-8/12 xl:w-6/12 mx-auto mt-8">
    <ErrorMessage
        title="Keine Berechtigung"
        message="Ihnen fehlt die Berechtigung für diese Seite"
    />
  </section>
</template>

<script setup lang="ts">
import type { SchemaEvent, SchemaEventUpdate } from "#open-fetch-schemas/medlogapi";
import type { EventFormSchema } from "~/components/Event/Form.vue";
import { eventTypeModeLabels } from "~/constants";
import { ConfirmationModal } from "#components";
import { isFastAPIEventNotEmptyError, isFetchError } from "~/type-helper";

const configStore = useConfigStore();
const eventStore = useEventStore();
const modal = useModal();
const studyPermissionStore = useStudyPermissionStore();
const studyStore = useStudyStore();
const toast = useToast();
const route = useRoute();

const createEventError = ref();
const editEventError = ref();
const eventFormInitialState = ref<Partial<EventFormSchema>>();
const eventIdToEdit = ref<string>('');
const loading = ref(false);
const showCreateEventModal = ref(false);
const showEditEventModal = ref(false);
const sortingMode = ref(false);

const studyId = computed(() => {
  return route.params.study_id as string;
});

// A deactivated study is closed for changes, events included (issue #197). The backend
// answers 403 on every event mutation, so do not offer the actions in the first place.
const studyIsActive = computed(() => {
  return studyStore.isStudyActive(studyId.value);
});

const myEvents = ref<SchemaEvent[]>([])

async function loadEvents() {
  loading.value = true;
  myEvents.value = await useGetEventsByStudy(studyId.value);
  loading.value = false;
}

function beginReordering() {
  sortingMode.value = true;
}

function cancelReordering() {
  sortingMode.value = false;
  loadEvents();
}

async function endReordering() {
  try {
    await useCreateEventOrder(studyId.value, myEvents.value.map(event => event.id ?? ''));
    await loadEvents();
    await eventStore.loadAllEventsForStudy(studyId.value);
    sortingMode.value = false;
  } catch (error) {
    toast.add({
      title: "Konnte Reihenfolge nicht speichern",
      description: useGetErrorMessage(error),
    });
  }
}

async function openCreateEventModal() {
  showCreateEventModal.value = true;
  createEventError.value = undefined;
}

async function openEditEventModal(event: SchemaEvent) {
  eventIdToEdit.value = event.id!;
  eventFormInitialState.value = {
    name: event.name,
    external_id: event.external_id ?? null,
    event_type_mode: event.event_type_mode ?? null,
    event_type: event.event_type ?? null,
  };
  showEditEventModal.value = true;
  editEventError.value = undefined;
}

async function createEvent(data: EventFormSchema) {
  try {
    createEventError.value = undefined;
    await useCreateEvent(data, studyId.value);
    showCreateEventModal.value = false;
    await loadEvents()
    await eventStore.loadAllEventsForStudy(studyId.value);
  } catch (error) {
    createEventError.value = error;
  }
}

async function deleteEvent(event: SchemaEvent) {
  modal.open(ConfirmationModal, {
    onCancel: modal.close,
    onConfirm: async () => {
      await modal.close();
      try {
        await useDeleteEvent(event.study_id, event.id!);
      } catch (error) {
        if ((isFetchError(error) || isNuxtError(error)) && error.statusCode === 409 && isFastAPIEventNotEmptyError(error.data)) {
          toast.add({
            title: "Konnte Event nicht löschen",
            description: `Es sind noch ${error.data.detail.interview_ids.length} Interview(s) zu diesem Event vorhanden.`,
          });
        } else {
          toast.add({
            title: "Konnte Event nicht löschen",
            description: useGetErrorMessage(error),
          });
        }
      }
      await loadEvents();
      await eventStore.loadAllEventsForStudy(studyId.value);
    },
    description: "Nur Events, für die kein Interview vorliegt, können gelöscht werden. Entfernen Sie ggf. vorher betroffene Interviews.",
    question: `Soll das Event "${event.name}" wirklich gelöscht werden?`,
    isDangerousToConfirm: true,
  })
}

async function updateEvent(data: EventFormSchema) {
  try {
    editEventError.value = undefined;
    const { event_type_mode, event_type, ...rest } = data;
    const body: SchemaEventUpdate = rest;
    // Only send the event type settings if they were changed. The backend validates them
    // against the current server config, so an event whose type was removed from the
    // config (or with the feature switched off) can still be renamed.
    const initialState = eventFormInitialState.value;
    if (event_type_mode !== initialState?.event_type_mode || event_type !== initialState?.event_type) {
      body.event_type_mode = event_type_mode;
      body.event_type = event_type;
    }
    await usePatchEvent(studyId.value, eventIdToEdit.value, body);
    showEditEventModal.value = false;
    await loadEvents()
    await eventStore.loadAllEventsForStudy(studyId.value);
  } catch (error) {
    editEventError.value = error;
  }
}

function eventTypeBadgeLabel(event: SchemaEvent): string | undefined {
  if (!event.event_type_mode) {
    return undefined;
  }
  const modeLabel = eventTypeModeLabels[event.event_type_mode];
  return event.event_type ? `${modeLabel}: ${event.event_type}` : modeLabel;
}

onMounted(() => {
  loadEvents();
  configStore.loadEventTypes().catch((error) => {
    toast.add({
      title: "Konnte Arten der Interviews nicht laden",
      description: useGetErrorMessage(error),
    });
  });
});
</script>

<style scoped>

</style>

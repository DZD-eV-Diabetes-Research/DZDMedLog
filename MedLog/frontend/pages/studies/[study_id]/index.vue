<template>
    <Layout>
        <div class="center">
            <h3>{{ study.display_name }}</h3>
        </div>
        <Draggable
        :list="events.items"
        :disabled="!enabled"
        item-key="name"
        class="list-group"
        ghost-class="ghost"
        @start="dragging = true"
        @end="dragging = false"
      >
        <template #item="{ element }">
          <div class="list-group-item" :class="{ 'not-draggable': !enabled }">
            <UIBaseCard class="events" :class="{ 'sorted': isSorted }">{{ element.name }}</UIBaseCard>
          </div>
        </template>
      </Draggable>
        <UIBaseCard v-if="events.items.length === 0">
            <h5>Keine Events in der Studie aufgezeichnet</h5>
        </UIBaseCard>
        <UIBaseCard v-if="userStore.isAdmin" class="noHover" :naked="true">
            <UButton @click="showEventModal = true" label="Event anlegen" color="green" variant="soft"
                class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
            <UButton @click="toggleSort" :label="sortButton" color="blue" variant="soft"
                class="border border-blue-500 hover:bg-blue-300 hover:border-white hover:text-white" />
            <UModal v-model="showEventModal">
                <div class="p-4" style="text-align: center;">
                    <UForm :schema="eventSchema" :state="eventState" class="space-y-4" @submit="createEvent">
                        <h3>Event anlegen</h3>
                        <UFormGroup label="Event Name" name="name">
                            <UInput v-model="eventState.name" required placeholder="Interview Campaign Year Quarter" />
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

let id = 1;
const enabled = ref(false);
const dragging = ref(false);

const draggingInfo = computed(() => {
  return dragging.value ? 'under drag' : '';
});


import { boolean, number, object, string, type InferType } from "yup";
import { computed } from 'vue';

const studyStore = useStudyStore()
const tokenStore = useTokenStore()
const userStore = useUserStore()
const runtimeConfig = useRuntimeConfig()
const route = useRoute()

const isSorted = ref(false);
const sortButton = ref("Events Sortieren")

const showEventModal = ref(false)
const study = await studyStore.getStudy(route.params.study_id)

const { data: events, refresh } = await useFetch(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/event`, {
    method: "GET",
    headers: { 'Authorization': "Bearer " + tokenStore.access_token },
})

const eventState = reactive({ name: "" });

const eventSchema = object({
    name: string().required("Required"),
});

const test = ref([])

async function toggleSort() {
    if (sortButton.value === "Sortierung Speichern"){
        sortButton.value = "Events Sortieren"

        events.value.items.map(element => {
            test.value.push(element)
            });
        await $fetch(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/event/order`, {
            method: "POST",
            headers: { 'Authorization': "Bearer " + tokenStore.access_token },
            body: test.value
        })
    } else {
        sortButton.value = "Sortierung Speichern"
    }
    isSorted.value = !isSorted.value;
    enabled.value = !enabled.value
}

async function createEvent() {
    try {
        await useCreateEvent(eventState.name.trim(), route.params.study_id);
        showEventModal.value = false;
        await refresh();
    } catch (error) {
        console.error("Failed to create event: ", error);
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

</style>
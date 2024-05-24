<template>
    <Layout>
        <div class="center">
            <h3>{{ study.display_name }}</h3>
        </div>
        <UIBaseCard v-for="event in reversedEvents" v-if="reversedEvents.length > 0">
           <h4> {{ useStringDoc(event.name) }} </h4>
        </UIBaseCard>
        <UIBaseCard v-else>
            <h5>Keine Events in der Studie aufgezeichnet</h5>
        </UIBaseCard>
        <UIBaseCard v-if="userStore.isAdmin" class="noHover" :naked="true">
            <UButton @click="showEventModal = true" label="Event anlegen" color="green" variant="soft"
                class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
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


import { boolean, number, object, string, type InferType } from "yup";
import { computed } from 'vue';

const studyStore = useStudyStore()
const tokenStore = useTokenStore()
const userStore = useUserStore()
const runtimeConfig = useRuntimeConfig()
const route = useRoute()

const showEventModal = ref(false)
const study = await studyStore.getStudy(route.params.study_id)

const { data: events, refresh } = await useFetch(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/event`, {
    method: "GET",
    headers: { 'Authorization': "Bearer " + tokenStore.access_token },
})

const reversedEvents = computed(() => {
    return [...events.value.items].reverse();
});

const eventState = reactive({ name: "" });

const eventSchema = object({
    name: string().required("Required"),
});

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

</style>
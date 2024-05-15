<template>
    <Layout>
        <UIBaseCard @click="openInterviewModal(item)" v-for="item in reversedEvents" style="text-align: center">
            <h3>{{ useStringDoc(item.name) }}</h3>
        </UIBaseCard>
            <UModal v-model="showInterviewModal">
                <div class="p-4" style="text-align: center">
                    <UForm :schema="interviewSchema" :state="interviewState" class="space-y-4"
                        @submit="createInterview()">
                        <h3>Neues Interview anlegen für</h3>
                        <h4>{{ useStringDoc(currentItem.name) }}</h4>
                        <UFormGroup label="Probanden-ID" name="subjectID">
                            <UInput v-model="interviewState.subjectID" required />
                        </UFormGroup>
                        <UFormGroup label="Interview-Nummer" name="interviewNumber">
                            <UInput v-model="interviewState.interviewNumber" type="number" required />
                        </UFormGroup>
                        <URadioGroup v-model="selected" style="border: 'border border-black'"
                            legend="Haben Sie Diabetes-Medikamente in den vergangenen 12 Monaten bzw. andere Medikamente in den letzten 7 Tagen eingenommen?"
                            :options="options" />
                        <UButton type="submit" label="Interview anlegen" color="green" variant="soft"
                            class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
                    </UForm>
                </div>
            </UModal>

        <UIBaseCard v-if="userStore.isAdmin" class="noHover">
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

const reversedEvents = computed(() => {
    return [...events.value.items].reverse();
});

const userStore = useUserStore()
const tokenStore = useTokenStore()
const route = useRoute()
const router = useRouter()

const showInterviewModal = ref(false)
const showEventModal = ref(false)
const currentItem = ref("test")


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


const eventState = reactive({ name: "" });

const eventSchema = object({
    name: string().required("Required"),
});

const { data: events, refresh } = await useFetch(`http://localhost:8888/study/${route.params.study_id}/event`, {
    method: "GET",
    headers: { 'Authorization': "Bearer " + tokenStore.access_token },
})

function newInterview(item) {
    router.push({ path: "/interview/" + route.params.study_id + '/event/' + item.id })
}

function openInterviewModal(item) {
    currentItem.value = item;    
    showInterviewModal.value = true;
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

async function createInterview() {    
    let takenMeds = selected.value === "true"
    const myItem = currentItem.value
    
    try {        
        showInterviewModal.value = false;
        const responseData = await useCreateInterview(route.params.study_id, myItem.id, interviewState.subjectID, takenMeds, interviewState.interviewNumber);
        router.push({ path: "/interview/" + route.params.study_id + '/event/' + myItem.id + "/" + responseData.id})
    } catch (error) {
        console.error("Failed to create event: ", error);
    }
}

watch(showInterviewModal, (newValue) => {
    if (!newValue) {
        currentItem.value = null; // Reset the currentItem when the modal is closed
    }
});

</script>

<style scoped>
.base-card:hover {
    background-color: #ededed;
    cursor: pointer;
}

.noHover:hover {
    background-color: white;
    cursor: default;
}
</style>
<template>
    <Layout>
        <UIBaseCard style="text-align: center" class="noHover">
            <UButton 
                @click="showModal = true"
                label="New Interview"
                color="green"
                variant="soft"
                class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white"/>
                <UModal v-model="showModal">
                    <div class="p-4" style="text-align: center">
                        <UForm :schema="schema"
                            :state="state"
                            class="space-y-4"
                            @submit="createInterview">
                        <h3>Neues Interview anlegen</h3>
                        <UFormGroup label="Probanden-ID" name="subjectID">
                            <UInput v-model="state.subjectID" required/>
                        </UFormGroup>
                        <UFormGroup label="Interview-Nummer" name="interviewNumber">
                            <UInput v-model="state.interviewNumber" type="number" required/>
                        </UFormGroup>
                        <URadioGroup v-model="selected" style="border: 'border border-black'" legend="Haben Sie Diabetes-Medikamente in den vergangenen 12 Monaten bzw. andere Medikamente in den letzten 7 Tagen eingenommen?" :options="options" />
                        <UButton type="submit" label="Interview anlegen" color="green" variant="soft"
                            class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
                        </UForm>
                    </div>
                </UModal>
        </UIBaseCard>
        <UIBaseCard @click="seeStuff(interview)" v-for="interview in interviews">
            <h5>Interview Number: {{ interview.interview_number }}</h5>
            <p>Probanden-ID: {{ interview.proband_external_id }}</p>
        </UIBaseCard>
    </Layout>
</template>

<script setup lang="ts">
import { boolean, number, object, string, type InferType } from "yup";

const route = useRoute()
const router = useRouter()
const tokenStore = useTokenStore()
const userStore = useUserStore()

const showModal = ref(false)

const state = reactive({
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

const schema = object({
    subjectID: string().required("Required"),
    interviewNumber: number().required("Required")
});

async function seeStuff(interview) {
    console.log(interview);
}


async function createInterview() { 
    let takenMeds
        if (selected.value === "true"){
            takenMeds = true
        } else {
            takenMeds = false
        }
    try {
        await useCreateInterview(route.params.study_id, route.params.event_id, state.subjectID, takenMeds, state.interviewNumber);
        showModal.value = false;
        await refresh();
    } catch (error) {
        console.error("Failed to create event: ", error);
    }   
}

const { data: interviews, refresh } = await useFetch(`http://localhost:8888/study/${route.params.study_id}/interview`, {
    method: "GET",
    headers: { 'Authorization': "Bearer " + tokenStore.access_token },
})

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
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
        <UIBaseCard class="active" v-for="study in studyStore.studies.items" :key="study.id" style="text-align: center">
            <h3>{{ study.display_name }}</h3>
            <UForm :schema="schema" :state="state" class="space-y-4" @submit="pushFurther(study)">
                <UFormGroup label="ProbandenID" name="probandID">
                    <UInput v-model="state.probandID" />
                </UFormGroup>
                <UButton color="green" variant="soft"
                    class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white"
                    type="submit">
                    Suchen
                </UButton>
            </UForm>

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

const userStore = useUserStore()
const studyStore = useStudyStore()
const tokenStore = useTokenStore()
const probandStore = useProbandStore()
const router = useRouter()
const runtimeConfig = useRuntimeConfig()

const schema = object({
    probandID: string().required('Required'),
})

type Schema = InferType<typeof schema>

const state = reactive({
    probandID: undefined,
})

async function pushFurther(study) {
    try {
        const response = await $fetch(`${runtimeConfig.public.baseURL}study/${study.id}/proband/${state.probandID}/interview`, {
            method: "GET",
            headers: { 'Authorization': "Bearer " + tokenStore.access_token },
        });
        probandStore.interviews = response
        probandStore.probandID = state.probandID

        router.push({ path: "/interview/proband/" + state.probandID + "/study/" + study.id })
    } catch (error) {
        console.log(error);
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
</style>

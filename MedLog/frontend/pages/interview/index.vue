<template>
    <Layout>
        <div class="flex justify-center">
            <h1 class="text-4xl font-normal">Neue Interviews Starten</h1>
        </div>
        <UIBaseCard v-if="studyStore.studies?.count === 0 || !studyStore.studies">
            <div v-if="userStore.isAdmin" class="space-y-4">
                <h2 class="text-2xl">Aktuell sind keine Studien aufgelistet bitte, legen Sie eine Studie an</h2>
                <UButton color="green" variant="soft"
                    class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" @click="moveToStudies()">
                    Studienverwaltung
                </UButton>
            </div>
            <h2 v-if="!userStore.isAdmin" class="text-2xl">Aktuell sind keine Studien aufgelistet bitte, wenden Sie sich
                an einen Admin</h2>
        </UIBaseCard>
        <UIBaseCard class="active" v-for="study in studyStore.studies.items" :key="study.id" style="text-align: center">
            <h3 class="text-2xl font-light">Studie: {{ study.display_name }}</h3>
            <UForm :schema="schema" :state="state" class="space-y-4" @submit="pushFurther(study)">
                <UFormGroup label="ProbandenID" name="probandID">
                    <UInput v-model="state.probandID" />
                </UFormGroup>
                <UButton color="green" variant="soft"
                    class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white"
                    type="submit">
                    Proband aufrufen
                </UButton>
            </UForm>
        </UIBaseCard>
    </Layout>
</template>

<script setup lang="ts">
import { object, string, type InferType, number } from 'yup'

const userStore = useUserStore()
const studyStore = useStudyStore()
const tokenStore = useTokenStore()
const probandStore = useProbandStore()
const router = useRouter()
const runtimeConfig = useRuntimeConfig()
const { $api } = useNuxtApp();


const schema = object({
    probandID: string().required('Required'),
})

type Schema = InferType<typeof schema>

const state = reactive({
    probandID: undefined,
})

async function pushFurther(study) {
    try {
        const response = await $api(`${runtimeConfig.public.baseURL}study/${study.id}/proband/${state.probandID}/interview`);
        probandStore.interviews = response
        probandStore.probandID = state.probandID

        router.push({ path: "/interview/proband/" + state.probandID + "/study/" + study.id })
    } catch (error) {
        console.log(error);
    }
}

const moveToStudies = function() {
    router.push({ path: "/studies" })
}

</script>

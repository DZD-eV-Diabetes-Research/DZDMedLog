<template>
    <Layout>
        <div class="center">
            <h1 class="text-4xl font-normal">Interviews</h1>
        </div>
        <UIBaseCard v-if="!studyStore.studies">
            <h2 v-if="userStore.isAdmin">Aktuell sind keine Studien aufgelistet bitte, legen Sie eine Studie an</h2>
            <h2 v-if="!userStore.isAdmin">Aktuell sind keine Studien aufgelistet bitte, wenden Sie sich an einen Admin
            </h2>
        </UIBaseCard>
        <UIBaseCard class="active" v-for="study in studyStore.studies.items" :key="study.id" style="text-align: center">
            <h3 class="text-2xl font-light">{{ study.display_name }}</h3>
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

<style lang="css" scoped>
.center {
    text-align: center;
    margin: auto;
    width: 50%;
    padding: 10px;
}
</style>

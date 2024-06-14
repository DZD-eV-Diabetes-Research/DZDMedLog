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
        <UIBaseCard class="active" v-for="study in studyStore.studies.items" :key="study.id"
            style="text-align: center">
            <h3>{{ study.display_name }}</h3>
            <UForm :schema="schema" :state="state" class="space-y-4"  @submit="test(study)">
                <UFormGroup label="ProbandenID" name="probandID">
                    <UInput v-model="state.probandID"/>
                </UFormGroup>
                <UButton
              color="green"
              variant="soft"
              class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white"
              type="submit"
            >
                Suchen
            </UButton>
            </UForm>
            
        </UIBaseCard>
    </Layout>
</template>

<script setup lang="ts">
import { object, string, type InferType, number } from 'yup'
import type { FormSubmitEvent } from '#ui/types'

const schema = object({
    probandID: string().required('Required'),
})

type Schema = InferType<typeof schema>

const state = reactive({
    probandID: undefined,
})

async function test(study) {
    console.log("test", study);
    
}

async function onSubmit (event: FormSubmitEvent<Schema>) {
  // Do something with event.data
  console.log(event.data)
}

const userStore = useUserStore()
const studyStore = useStudyStore()
const tokenStore = useTokenStore()
const router = useRouter()
const route = useRoute()
const runtimeConfig = useRuntimeConfig()

const selectedStudy = ref()

</script>

<style lang="scss" scoped>
.center {
    text-align: center;
    margin: auto;
    width: 50%;
    padding: 10px;
}
</style>
  
<template>
    <Layout>
        <div class="center">
            <h1>Studien</h1>
        </div>
        <UIBaseCard v-if="!studyStore.studies">
            <h2 v-if="userStore.isAdmin">Aktuell sind keine Studien aufgelistet bitte, legen Sie eine Studie an</h2>
            <h2 v-if="!userStore.isAdmin">Aktuell sind keine Studien aufgelistet bitte, wenden Sie sich an einen Admin
            </h2>
        </UIBaseCard>
        <UIBaseCard @click="selectStudy(study)" v-for="study in studyStore.studies.items" :key="study.id"
            style="text-align: center">
            <h3>{{ study.display_name }}</h3>
        </UIBaseCard>
        <UIBaseCard v-if="userStore.isAdmin" class="noHover" :naked="true">
            <UButton @click="showModal = true" label="Studie anlegen" color="green" variant="soft"
                class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
            <UModal v-model="showModal">
                <div class="p-4" style="text-align: center;">
                    <UForm :schema="schema"
                            :state="state"
                            class="space-y-4"
                            @submit="createStudy">
                        <h3>Studie anlegen</h3>
                        <UFormGroup label="Studienname" name="study_name">
                            <UInput v-model="state.study_name" required />
                        </UFormGroup>
                        <UButton type="submit" label="Studie anlegen" color="green" variant="soft"
                            class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
                    </UForm>
                </div>
            </UModal>
        </UIBaseCard>
    </Layout>
</template>

<script setup lang="ts">

import { object, string, type InferType } from "yup";

const userStore = useUserStore()
const studyStore = useStudyStore()
const router = useRouter()

const showModal = ref(false)
const state = reactive({
    study_name: "",
});

const schema = object({
    study_name: string().required("Required"),
});

function createStudy() {
    showModal.value = false
    studyStore.createStudy(state.study_name.trim())
    studyStore.listStudies()
}

function selectStudy(study) {
    router.push({ path: "/studies/" + study.id })
}

</script>

<style lang="scss" scoped>
.base-card:hover {
    background-color: #ededed;
    cursor: pointer;
}

.noHover:hover {
    background-color: white;
    cursor: default;
}

.center {
    text-align: center;
    margin: auto;
    width: 50%;
    padding: 10px;
}
</style>
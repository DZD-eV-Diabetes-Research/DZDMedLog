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
        <UIBaseCard v-if="userStore.isAdmin" class="noHover">
            <UButton @click="showModal = true" label="Studie anlegen" color="green" variant="soft"
                class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
            <UModal v-model="showModal">
                <div class="p-4" style="text-align: center;">
                    <UForm :schema="schema"
                            :state="state"
                            class="space-y-4"
                            @submit="createStudy">
                        <h3>Studie anlegen</h3>
                        <UFormGroup label="Display Name" name="display_name">
                            <UInput v-model="state.display_name" required />
                        </UFormGroup>
                        <UFormGroup label="Abkürzing" name="abbreviation">
                            <UInput v-model="state.abbreviation" required />
                        </UFormGroup>
                        <UCheckbox v-model="state.deactivated" name="deactivated" label="Deactivated" />
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
    display_name: "",
    deactivated: false,
    no_permissions: false,
    id: "",
    abbreviation: ""
});

const schema = object({
    display_name: string().required("Required"),
    abbreviation: string().required("Required"),
});

function createStudy() {
    showModal.value = false
    console.log(state.display_name.trim());
    console.log(state.abbreviation.trim().replace(" ", ""));
    console.log(state.deactivated)
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
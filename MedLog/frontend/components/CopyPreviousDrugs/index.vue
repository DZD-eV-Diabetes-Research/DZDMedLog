<template>
    <div class="flex flex-col justify-center items-center">
        <div class="flex flex-row justify-center">
            <UButton @click="openCopyIntakeModal()" label="Medikation Übernehmen" color="green" variant="soft"
                style="margin-right: 10px"
                class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
            <div class="flex items-center ">
                <UTooltip :delay-duration="0" text="Medikatmente aus dem letzten Events übernehmen">
                    <UIcon name="i-heroicons-question-mark-circle" class="size-5" />
                </UTooltip>
            </div>
        </div>
        <UModal v-model="copyPreviousIntakesModal" class="custom-modal">
            <div class="p-10 text-center max-w-5xl">
                <div v-if="previousIntakes">
                    <UTable v-model="selecteIntakes" :rows="previousIntakes"/>
                    <UButton @click="test()" label="Medikation Übernehmen" color="green" variant="soft"
                        style="margin-right: 10px"
                        class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white  mt-4" />
                </div>
                <div v-if="!previousIntakes && !errorMessage">
                    loading
                </div>
                <div v-if="errorMessage">
                    <h3 class="text-red-500">Es gab ein Problem beim Laden der Medikamente. Bitte melden Sie sich bei
                        ihrem Admin</h3>
                </div>
            </div>
        </UModal>
        {{ previousIntakes }}
    </div>
</template>

<script setup lang="ts">

const runtimeConfig = useRuntimeConfig();
const tokenStore = useTokenStore();
const route = useRoute();

const copyPreviousIntakesModal = ref(false)
const errorMessage = ref(false)

const previousIntakes = ref<any[]>([])
// const previousIntakes = [ { "Medikament": "65422", "Einnahmebeginn": "2025-03-18", "Einnahmeende": "Unbekannt", "Dosis": "Unbekannt" }, { "Medikament": "5dfd1", "Einnahmebeginn": "2025-03-18", "Einnahmeende": "Unbekannt", "Dosis": 1 }, { "Medikament": "5dfd1", "Einnahmebeginn": "2025-03-18", "Einnahmeende": "Unbekannt", "Dosis": 1 }, { "Medikament": "c7361", "Einnahmebeginn": "2025-03-18", "Einnahmeende": "Unbekannt", "Dosis": 2 }, { "Medikament": "d1a12", "Einnahmebeginn": "2025-03-18", "Einnahmeende": "Unbekannt", "Dosis": 2 }, { "Medikament": "97a60", "Einnahmebeginn": "2025-03-18", "Einnahmeende": "Unbekannt", "Dosis": "Unbekannt" }, { "Medikament": "2451c", "Einnahmebeginn": "2025-03-18", "Einnahmeende": "Unbekannt", "Dosis": "Unbekannt" } ]
const selecteIntakes = ref([])

async function openCopyIntakeModal() {
    copyPreviousIntakesModal.value = true
    errorMessage.value = false
    try {
        //`${runtimeConfig.public.baseURL}study/${route.params.study_id}/proband/${route.params.proband_id}/interview/current/intake`
        const intakes = await $fetch(`${runtimeConfig.public.baseURL}study/b6f2c61b-d388-4412-8c9a-461ece251116/proband/1234/interview/current/intake`, {
            method: "GET",
            headers: { 'Authorization': "Bearer " + tokenStore.access_token },
        })

        previousIntakes.value = Array.isArray(intakes) ? intakes.map((intake: any) => ({
            Medikament: intake.drug_id.substring(0, 5),
            Einnahmebeginn: intake.intake_start_time_utc || 'Unbekannt',
            Einnahmeende: intake.intake_end_time_utc || 'Unbekannt',
            Dosis: intake.dose_per_day || 'Unbekannt',
        })) : []

    } catch (error) {
        console.log(error);
        errorMessage.value = true
        previousIntakes.value = []
    }
}

function test() {
    console.log("speichert");
    copyPreviousIntakesModal.value = false
}

</script>
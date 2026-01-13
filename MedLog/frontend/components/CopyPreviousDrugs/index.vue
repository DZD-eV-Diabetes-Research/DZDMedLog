<!-- This component serves to copy the intakes of the previous event -->

<template>
    <div class="flex flex-col justify-center items-center">
        <div>
            <UTooltip text="Es liegen keine Medikamente zur Übernahme vor" :popper="{ arrow: true }" :prevent="!deactivated">
                <UButton
                    :disabled="deactivated"
                    icon="i-heroicons-document-duplicate"
                    :color="deactivated ? 'gray' : 'green'" variant="outline" label="Medikationsübernahme"
                    @click="openCopyIntakeModal()"
                />
            </UTooltip>
        </div>
        <UModal v-model="openCopyPreviousIntakesModal" :ui="{ width: 'lg:max-w-6xl' }" prevent-close>
            <UCard>
                <template #header>
                    <div class="flex items-center justify-between">
                      <span class="text-lg">Medikationsübernahme</span>
                      <UButton color="gray" variant="ghost" icon="i-heroicons-x-mark-20-solid" class="-my-1" @click="openCopyPreviousIntakesModal = false" />
                    </div>
                </template>

                <div class="text-center">
                    <ErrorMessage v-if="error" :error="error" :title="errorTitle" />
                    <UProgress v-if="loading" animation="carousel" />
                    <div v-if="previousIntakes.length > 0">
                        <div class="space-y-2 mb-6">
                            <span class="text-md font-bold">Event:</span> {{ lastEventName }}
                            <br>
                            <span class="text-md font-bold">Letzte Änderung:</span> {{ lastEventDate }}
                        </div>
                        <UTable
                            v-model="selectedIntakes" :columns="columns" :rows="previousIntakes"
                            class="border border-slate-400 rounded-md" />
                        <UButton label="Ausgewählte Medikamente übernehmen" class="mt-8" @click="saveIntakes()" />
                    </div>
                    <div v-if="previousIntakes.length === 0">
                        <h3>Es gibt keine Einträge im letzten Event</h3>
                    </div>
                </div>
            </UCard>
        </UModal>
    </div>
</template>

<script setup lang="ts">
import { useDayjs } from '#dayjs'
import localizedFormat from 'dayjs/plugin/localizedFormat'

const dayjs = useDayjs();
const { $medlogapi } = useNuxtApp();
const route = useRoute();

dayjs.extend(localizedFormat);

const props = defineProps<{ onUpdate: () => void, deactivated: boolean }>();

const openCopyPreviousIntakesModal = ref(false)
const error = ref();
const errorTitle = ref("");
const loading = ref(false);

const previousIntakes = ref<any[]>([])
const selectedIntakes = ref([])
const lastEventName = ref("")
const lastEventDate = ref("")

// Backend interaction

async function openCopyIntakeModal() {
    openCopyPreviousIntakesModal.value = true
    error.value = undefined;
    errorTitle.value = "";
    loading.value = true;

    try {
        const intakes = await $medlogapi(`/api/study/{studyId}/proband/{probandId}/interview/last/intake/details`,{
            path: {
                studyId: route.params.study_id,
                probandId: route.params.proband_id,
            }
        })


        lastEventName.value = intakes[0]?.event.name
        lastEventDate.value = dayjs.utc(intakes[0]?.interview.interview_end_time_utc).local().format('LLL');

        // Transform the API response into a format suitable for both the UI and the POST request body
        previousIntakes.value = Array.isArray(intakes) ? intakes.map((intake: any) => ({
            Medikament: intake.drug.trade_name,
            Custom: intake.drug?.is_custom_drug ? "Ja" : "Nein",
            Einnahmebeginn: intake.intake_start_time_utc || 'Unbekannt',
            Einnahmeende: intake.intake_end_time_utc || 'Unbekannt',
            Dosis: intake.dose_per_day || 'Unbekannt',
            ID: intake.id,
            postBody: {
                "drug_id": intake.drug_id,
                "source_of_drug_information": intake.source_of_drug_information,
                "intake_start_time_utc": intake.intake_start_time_utc,
                "intake_end_time_utc": intake.intake_end_time_utc,
                "administered_by_doctor": intake.administered_by_doctor,
                "intake_regular_or_as_needed": intake.intake_regular_or_as_needed,
                "dose_per_day": intake.dose_per_day,
                "regular_intervall_of_daily_dose": intake.regular_intervall_of_daily_dose,
                "as_needed_dose_unit": intake.as_needed_dose_unit,
                "consumed_meds_today": intake.consumed_meds_today,
            },
            // Simple css class to highlight the custom drugs yellow 
            class: intake.drug?.is_custom_drug
                ? "bg-yellow-50"
                : null,
        })) : []
        selectedIntakes.value = previousIntakes.value

    } catch (e) {
        error.value = e;
        errorTitle.value = "Fehler beim Abruf früherer Einnahmen";
        previousIntakes.value = []
    } finally {
      loading.value = false;
    }
}

async function saveIntakes() {
    error.value = undefined;
    errorTitle.value = "";
    loading.value = true;

    try {
      for (const element of selectedIntakes.value) {
        await $medlogapi(`/api/study/{studyId}/interview/{interviewId}/intake`, {
          method: "POST",
          body: element.postBody,
          path: {
            studyId: route.params.study_id,
            interviewId: route.params.interview_id,
          }
        })
      }

      // Call the parent component's update handler (prop) after saving
      props.onUpdate();
      openCopyPreviousIntakesModal.value = false
    } catch (e) {
        error.value = e;
        errorTitle.value = "Fehler beim Übernehmen der Einnahmen";
    } finally {
      loading.value = false;
    }
}


// Template / UI Interaction

const columns = [{
    key: 'Medikament',
    label: 'Medikament'
}, {
    key: 'Custom',
    label: 'Custom'
}, {
    key: 'Einnahmebeginn',
    label: 'Einnahmebeginn'
}, {
    key: 'Einnahmeende',
    label: 'Einnahmeende'
}, {
    key: 'Dosis',
    label: 'Dosis'
},]

</script>

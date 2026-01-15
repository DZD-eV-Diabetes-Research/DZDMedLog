<!-- This is the main drug intake form component that is used to create or edit intakes -->
<template>
  <UForm ref="intakeForm" :state="state" :schema="schema" class="space-y-4" @submit="onSubmit">
    <UFormGroup
        label="Wirkstoff äquivalent, abweichender Produkt-Code"
        description="Das gewählte Präparat entspricht in Wirkstoff und Wirkstoffmenge dem eingenommenen, die PZN ist unbekannt."
    >
      <UToggle v-model="state.isActiveIngredientEquivalentChoice" />
    </UFormGroup>

    <UFormGroup label="Quelle der Arzneimittelangabe" name="drugSource">
      <USelect v-model="state.drugSource" :options="drugSourceOptions" />
    </UFormGroup>

    <UFormGroup label="Vom Arzt verordnet?" name="administeredByDoctor">
      <USelect v-model="state.administeredByDoctor" :options="administeredByDoctorOptions" />
    </UFormGroup>
    <UFormGroup label="Einnahme regelmäßig oder nach Bedarf?" name="frequency">
      <USelect v-model="state.frequency" :options="frequencyOptions" />
    </UFormGroup>
    <div class="flex flex-row space-x-4">
      <div class="flex-1">
        <UFormGroup label="Dosis pro Einnahme" style="border-color: red" name="dose">
          <UInput v-model="state.dose" type="number" min="0" :disabled="state.frequency !== 'regular'"/>
        </UFormGroup>
      </div>
      <div class="flex-1">
        <UFormGroup label="Intervall der Tagesdosen" name="intervall">
          <USelect v-model="state.intervall" :options="doseIntervalOptions" :disabled="state.frequency !== 'regular'" />
        </UFormGroup>
      </div>
    </div>
    <div class="flex flex-row space-x-4">
      <div class="flex-1">
        <UFormGroup label="Einnahme Beginn (Datum)" name="startTime">
          <UInput v-model="state.startTime" type="date" />
        </UFormGroup>
      </div>
      <div class="flex-1">
        <UFormGroup label="Einnahme Ende (Datum)" name="endTime">
          <UInput v-model="state.endTime" type="date" />
        </UFormGroup>
      </div>
    </div>
    <URadioGroup
        v-model="state.medsTakenToday" legend="Wurde dieses Medikament heute eingenommen?" name="medsTakenToday"
        :options="medsTakenTodayOptions" />
    <hr>
    <div class="flex justify-between">
      <UButton label="Abbrechen" variant="outline" @click.prevent="$emit('cancel')" />
      <UButton type="submit" label="Speichern" :disabled="!state.drugId" />
    </div>
  </UForm>
</template>

<script setup lang="ts">

import { object, number, date, string, type InferType, boolean } from "yup";
import type { FormSubmitEvent } from "#ui/types";
import {
  onMounted,
  reactive,
  useTemplateRef,
  watch
} from "#imports";
import {
  administeredByDoctorOptions,
  doseIntervalOptions,
  drugSourceOptions,
  frequencyOptions,
  medsTakenTodayOptions
} from "~/constants";

const props = defineProps<{
  drugId?: string;
  initialState?: any;
}>();

const emit = defineEmits(['cancel', 'save'])

const intakeForm = useTemplateRef('intakeForm')

const state = reactive({
  administeredByDoctor: administeredByDoctorOptions[0].value,
  dose: 0,
  drugId: "",
  drugSource: drugSourceOptions[0].value,
  endTime: null,
  frequency: frequencyOptions[0].value,
  intervall: doseIntervalOptions[0].value,
  isActiveIngredientEquivalentChoice: false,
  medsTakenToday: medsTakenTodayOptions[0].value,
  startTime: null,
});

const schema = object({
  administeredByDoctor: string().oneOf(administeredByDoctorOptions.map(item => item.value)),
  dose: number().min(0, "Required"),
  drugId: string().required("Kein Medikament ausgewählt"),
  drugSource: string().oneOf(drugSourceOptions.map(item => item.value)).required("Required"),
  endTime: date().optional().nullable(),
  frequency: string().oneOf(frequencyOptions.map(item => item.value)).required("Required"),
  intervall: string().oneOf(doseIntervalOptions.map(item => item.value)),
  isActiveIngredientEquivalentChoice: boolean().required(),
  medsTakenToday: string().oneOf(medsTakenTodayOptions.map(item => item.value)).required("Required"),
  startTime: date().optional().nullable(),
});

export type IntakeFormSchema = InferType<typeof schema>;

async function onSubmit(event: FormSubmitEvent<IntakeFormSchema>) {
  emit('save', event.data);
}

// Explicitly reset dates to null, to prevent a validation error
watch(() => state.startTime, (newValue) => {
  if (newValue === "") {
    state.startTime = null;
  }
})
watch(() => state.endTime, (newValue) => {
  if (newValue === "") {
    state.endTime = null;
  }
})

watch(() => props.drugId, async (newDrugId?: string) => {
  state.drugId = newDrugId ?? "";
  try {
    await intakeForm.value.validate();
  } catch (error) { // eslint-disable-line @typescript-eslint/no-unused-vars
    // Swallow error, the result is shown directly in the form
  }
}, { immediate: true });

onMounted(async () => {
  if (props.initialState) {
    // Populate form state with given state
    for (const key of Object.keys(state)) {
      if (props.initialState[key]) {
        state[key] = props.initialState[key];
      }
    }

    try {
      await intakeForm.value.validate();
    } catch (error) { // eslint-disable-line @typescript-eslint/no-unused-vars
      // Swallow error, the result is shown directly in the form
    }
  }
})
</script>

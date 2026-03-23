<!-- This is the main drug intake form component that is used to create or edit intakes -->
<template>
  <UForm ref="intakeForm" :state="state" :schema="schema" class="space-y-4" :validate-on="['blur', 'submit']" @submit="onSubmit">
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
        <UFormGroup label="Einnahme Beginn (Datum)" name="startDate">
          <DatePickerWithOptions
              v-model:date="state.startDate"
              v-model:option="state.startDateOption"
              :options="startDateOptions"
          />
        </UFormGroup>
      </div>
      <div class="flex-1">
        <UFormGroup label="Einnahme Ende (Datum)" name="endDate">
          <DatePickerWithOptions
              v-model:date="state.endDate"
              v-model:option="state.endDateOption"
              :options="endDateOptions"
          />
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

import { object, number, string, type InferType, boolean } from "yup";
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
  drugSourceOptions, endDateOptions,
  frequencyOptions,
  medsTakenTodayOptions, startDateOptions
} from "~/constants";

const props = defineProps<{
  drugId?: string;
  initialState?: { [key: string]: string; };
}>();

const emit = defineEmits(['cancel', 'save'])

const intakeForm = useTemplateRef('intakeForm')

const state = reactive({
  administeredByDoctor: administeredByDoctorOptions[0].value,
  dose: 0,
  drugId: "",
  drugSource: drugSourceOptions[0].value,
  endDate: undefined,
  endDateOption: undefined,
  frequency: frequencyOptions[0].value,
  intervall: doseIntervalOptions[0].value,
  isActiveIngredientEquivalentChoice: false,
  medsTakenToday: medsTakenTodayOptions[0].value,
  startDate: undefined,
  startDateOption: undefined,
});

const schema = object({
  administeredByDoctor: string().oneOf(administeredByDoctorOptions.map(item => item.value)),
  dose: number().min(0, "Required"),
  drugId: string().required("Kein Medikament ausgewählt"),
  drugSource: string().oneOf(drugSourceOptions.map(item => item.value)).required("Required"),
  endDate: string().when('endDateOption', { is: undefined, then: (schema) => schema.required(), otherwise: (schema) => schema.optional() }),
  endDateOption: string().oneOf(endDateOptions.map(item => item.value)).optional(),
  frequency: string().oneOf(frequencyOptions.map(item => item.value)).required("Required"),
  intervall: string().oneOf(doseIntervalOptions.map(item => item.value)),
  isActiveIngredientEquivalentChoice: boolean().required(),
  medsTakenToday: string().oneOf(medsTakenTodayOptions.map(item => item.value)).required("Required"),
  startDate: string().when('startDateOption', { is: undefined, then: (schema) => schema.required(), otherwise: (schema) => schema.optional() }),
  startDateOption: string().oneOf(startDateOptions.map(item => item.value)).optional(),
});

export type IntakeFormSchema = InferType<typeof schema>;

async function onSubmit(event: FormSubmitEvent<IntakeFormSchema>) {
  emit('save', event.data);
}

watch(() => props.drugId, async (newDrugId?: string) => {
  state.drugId = newDrugId ?? "";
}, { immediate: true });

onMounted(async () => {
  if (props.initialState) {
    // Populate form state with given state
    for (const key of Object.keys(state)) {
      if (props.initialState[key]) {
        state[key] = props.initialState[key];
      }
    }

    if (Object.hasOwn(props.initialState, 'isActiveIngredientEquivalentChoice') && Object.keys(props.initialState).length === 1) {
      // Exit before validation. This initial state does not represent a full record and was only used to set
      // the "active ingredient is equivalent" directly from the search results.
      return;
    }

    try {
      await intakeForm.value?.validate();
    } catch (error) { // eslint-disable-line @typescript-eslint/no-unused-vars
      // Swallow error, the result is shown directly in the form
    }
  }
})
</script>

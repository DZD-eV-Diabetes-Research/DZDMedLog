<!-- This is the main drug intake form component that is used to create or edit intakes -->
<template>
  <UForm ref="intakeForm" :state="state" :schema="schema" class="space-y-4" @submit="onSubmit">
    <div style="padding-top: 2.5%">
      <UFormGroup label="Quelle der Arzneimittelangabe">
        <USelect v-model="state.drugSource" :options="drugSourceOptions" :color="props.color" />
      </UFormGroup>
    </div>
    <UFormGroup label="Einnahme regelmäßig oder nach Bedarf?">
      <USelect v-model="state.frequency" :options="frequencyOptions" :color="props.color" />
    </UFormGroup>
    <div class="flex flex-row space-x-4">
      <div class="flex-1">
        <UFormGroup label="Dosis pro Einnahme" style="border-color: red" name="dose">
          <UInput
            v-model="state.dose" type="number" min="0" :disabled="state.frequency !== 'regular'"
            :color="state.frequency !== 'regular' ? 'gray' : props.color" />
        </UFormGroup>
      </div>
      <div class="flex-1">
        <UFormGroup label="Intervall der Tagesdosen">
          <USelect
            v-model="state.intervall" :options="doseIntervalOptions" :disabled="state.frequency !== 'regular'"
            :color="state.frequency !== 'regular' ? 'gray' : props.color" />
        </UFormGroup>
      </div>
    </div>
    <div class="flex flex-row space-x-4">
      <div class="flex-1">
        <UFormGroup label="Einnahme Beginn (Datum)" name="startTime">
          <UInput v-model="state.startTime" type="date" :color="props.color" />
        </UFormGroup>
      </div>
      <div class="flex-1">
        <UFormGroup label="Einnahme Ende (Datum)" name="endTime">
          <UInput v-model="state.endTime" type="date" :color="props.color" />
        </UFormGroup>
      </div>
    </div>
    <URadioGroup
        v-model="state.medsTakenToday" legend="Wurden heute Medikamente eingenommen?" name="medsTakenToday"
        :options="medsTakenTodayOptions" :color="props.color" />
    <hr>
    <div class="flex justify-between">
      <UButton label="Abbrechen" variant="outline" @click.prevent="$emit('cancel')" />
      <UButton type="submit" label="Speichern" :disabled="!state.drugId" />
    </div>
  </UForm>
</template>

<script setup lang="ts">

import dayjs from "dayjs";
import { object, number, date, string, type InferType } from "yup";
import type { FormSubmitEvent } from "#ui/types";

const props = defineProps<{
  color?: string;
  drugId?: string;
  initialState?: any;
}>();

const emit = defineEmits(['cancel', 'save'])

/**
 * TODO Switch to useTemplateRef() when updating to Vue 3.5
 * See https://vuejs.org/guide/essentials/template-refs.html#accessing-the-refs
 */
const intakeForm = ref(null)

const drugSourceOptions = [
  { value: "Study participant: verbal specification", label: "Probandenangabe" },
  { value: "Medication package: Scanned PZN", label: "Medikamentenpackung: PZN gescannt" },
  { value: "Medication package: Typed in PZN", label: "Medikamentenpackung: PZN getippt" },
  { value: "Medication package: Drug name", label: "Medikamentenpackung: Arzneimittelname" },
  { value: "Medication leaflet", label: "Beipackzettel" },
  { value: "Study participant: medication plan", label: "Medikamentenplan" },
  { value: "Study participant: Medication prescription", label: "Rezept" },
  { value: "Follow up via phone/message: Typed in PZN", label: "Nacherhebung: Tastatureingabe der PZN" },
  { value: "Follow up via phone/message: Medication name", label: "Nacherhebung: Arzneimittelname" },
];

const frequencyOptions = [
  { value: "as needed", label: "nach Bedarf" },
  { value: "regular", label: "regelmäßig" },
];

const doseIntervalOptions = [
  {
    value: "Unknown",
    label: "unbekannt"
  },
  {
    value: "Daily",
    label: "täglich"
  },
  {
    value: "every 2. day",
    label: "jeden 2. Tag"
  },
  {
    value: "every 3. day",
    label: "jeden 3. Tag"
  },
  {
    value: "every 4. day / twice a week",
    label: "jeden 4. Tag = 2x pro Woche"
  },
  {
    value: "intervals of one week or more",
    label: "Im Abstand von 1 Woche und mehr"
  },
];

const medsTakenTodayOptions = [
  {
    value: "Yes",
    label: "Ja",
  },
  {
    value: "No",
    label: "Nein",
  },
  {
    value: "UNKNOWN",
    label: "Unbekannt",
  },
];

const state = reactive({
  dose: 0,
  drugId: "",
  drugSource: drugSourceOptions[0].value,
  endTime: null,
  frequency: frequencyOptions[0].value,
  intervall: doseIntervalOptions[0].value,
  medsTakenToday: medsTakenTodayOptions[0].value,
  startTime: dayjs(Date()).format("YYYY-MM-DD")
});

const schema = object({
  dose: number().min(0, "Required"),
  drugId: string().required("Kein Medikament ausgewählt"),
  drugSource: string().oneOf(drugSourceOptions.map(item => item.value)).required("Required"),
  endTime: date().optional().nullable(),
  frequency: string().oneOf(frequencyOptions.map(item => item.value)).required("Required"),
  intervall: string().oneOf(doseIntervalOptions.map(item => item.value)),
  medsTakenToday: string().oneOf(medsTakenTodayOptions.map(item => item.value)).required("Required"),
  startTime: date().required("Required"),
});

export type IntakeFormSchema = InferType<typeof schema>;

async function onSubmit(event: FormSubmitEvent<IntakeFormSchema>) {
  emit('save', event.data);
}

watch(() => props.drugId, async (newDrugId: string) => {
  state.drugId = newDrugId;
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

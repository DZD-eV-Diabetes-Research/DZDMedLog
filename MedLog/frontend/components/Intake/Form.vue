<!-- This is the main drug intake form component that is used to create or edit intakes -->
<template>
  <UForm ref="intakeForm" :state="state" :schema="schema" class="space-y-4" :validate-on="['blur', 'submit']" @submit="onSubmit">
    <UFormGroup
        label="Wirkstoff äquivalent, abweichender Produkt-Code"
        description="Das gewählte Präparat entspricht in Wirkstoff und Wirkstoffmenge dem eingenommenen, die PZN ist unbekannt."
        name="is_activeingredient_equivalent_choice"
    >
      <UToggle v-model="state.is_activeingredient_equivalent_choice" />
    </UFormGroup>

    <UFormGroup label="Quelle der Arzneimittelangabe" name="source_of_drug_information">
      <USelect v-model="state.source_of_drug_information" :options="drugSourceOptions" />
    </UFormGroup>

    <UFormGroup label="Vom Arzt verordnet?" name="administered_by_doctor">
      <USelect v-model="state.administered_by_doctor" :options="administeredByDoctorOptions" />
    </UFormGroup>
    <UFormGroup label="Einnahme regelmäßig oder nach Bedarf?" name="intake_regular_or_as_needed">
      <USelect v-model="state.intake_regular_or_as_needed" :options="frequencyOptions" />
    </UFormGroup>
    <div class="flex flex-row space-x-4">
      <div class="flex-1">
        <UFormGroup label="Dosis pro Tag der Einnahme" style="border-color: red" name="dose_per_day">
          <UInput v-model.trim="state.dose_per_day" type="text" inputmode="decimal" :disabled="state.intake_regular_or_as_needed !== 'regular'"/>
        </UFormGroup>
      </div>
      <div class="flex-1">
        <UFormGroup label="Intervall der Tagesdosen" name="regular_intervall_of_daily_dose">
          <USelect v-model="state.regular_intervall_of_daily_dose" :options="doseIntervalOptions" :disabled="state.intake_regular_or_as_needed !== 'regular'" />
        </UFormGroup>
      </div>
    </div>
    <div class="flex flex-row space-x-4">
      <div class="flex-1">
        <UFormGroup label="Einnahme Beginn (Datum)" name="intake_start_date">
          <DatePickerWithOptions
              v-model:date="state.intake_start_date"
              v-model:option="state.startDateOption"
              :options="startDateOptions"
              earliest-date="1900-01-01"
          />
        </UFormGroup>
      </div>
      <div class="flex-1">
        <UFormGroup label="Einnahme Ende (Datum)" name="intake_end_date">
          <DatePickerWithOptions
              v-model:date="state.intake_end_date"
              v-model:option="state.endDateOption"
              :options="endDateOptions"
              earliest-date="1900-01-01"
          />
        </UFormGroup>
      </div>
    </div>
    <UFormGroup name="consumed_meds_today">
      <URadioGroup
          v-model="state.consumed_meds_today"
          legend="Wurde dieses Medikament heute eingenommen?"
          :options="medsTakenTodayOptions" />
    </UFormGroup>
    <hr>
    <div class="flex justify-between">
      <UButton label="Abbrechen" variant="outline" @click.prevent="$emit('cancel')" />
      <UButton type="submit" label="Speichern" :disabled="!state.drugId" />
    </div>
  </UForm>
</template>

<script setup lang="ts">

import { object, number, string, type InferType, boolean } from "yup";
import type { FormError, FormSubmitEvent } from "#ui/types";
import {
  onMounted,
  reactive,
  watch
} from "#imports";
import {
  administeredByDoctorOptions,
  doseIntervalOptions,
  drugSourceOptions, endDateOptions,
  frequencyOptions,
  medsTakenTodayOptions,
  plausibilityErrorMessages,
  startDateOptions
} from "~/constants";
import {isFastAPIPlausibilityError, isFastAPIValidationError, isFetchError} from "~/type-helper";
import type { UForm } from "#components";

const props = defineProps<{
  drugId?: string;
  initialState?: { [key: string]: string | number | boolean; };
  submitCallback: (data: IntakeFormSchema) => Promise<void>;
}>();

defineEmits(['cancel'])

const form = useTemplateRef<typeof UForm>('intakeForm')

const state = reactive<IntakeFormSchema>({
  administered_by_doctor: administeredByDoctorOptions[0].value,
  dose_per_day: 0,
  drugId: "",
  source_of_drug_information: drugSourceOptions[0].value,
  intake_end_date: undefined,
  endDateOption: undefined,
  intake_regular_or_as_needed: frequencyOptions[0].value,
  regular_intervall_of_daily_dose: doseIntervalOptions[0].value,
  is_activeingredient_equivalent_choice: false,
  consumed_meds_today: medsTakenTodayOptions[0].value,
  intake_start_date: undefined,
  startDateOption: undefined,
});

const schema = object({
  administered_by_doctor: string().oneOf(administeredByDoctorOptions.map(item => item.value)),
  dose_per_day: number()
      .transform((value, originalValue, schema) => {
        if (schema.isType(value)) {
          return value;
        }

        if (originalValue === '') {
          return NaN;
        }

        return Number(String(originalValue).replace(',', '.'));
      })
      .typeError('Eingabe ist keine gültige Zahl')
      .min(0, "Die Dosis muss 0 oder eine positive Zahl sein")
      .test(
        'two-decimal-places',
        'Maximal zwei Dezimalstellen angeben',
        (value) => {
          return String(value).match(/^\d+([.,]\d{1,2})?$/) !== null;
        }
      ),
  drugId: string().required("Kein Medikament ausgewählt"),
  source_of_drug_information: string().oneOf(drugSourceOptions.map(item => item.value)).required("Required"),
  intake_end_date: string().when('endDateOption', { is: undefined, then: (schema) => schema.required(), otherwise: (schema) => schema.optional() }),
  endDateOption: string().oneOf(endDateOptions.map(item => item.value)).optional(),
  intake_regular_or_as_needed: string().oneOf(frequencyOptions.map(item => item.value)).required("Required"),
  regular_intervall_of_daily_dose: string().oneOf(doseIntervalOptions.map(item => item.value)),
  is_activeingredient_equivalent_choice: boolean().required(),
  consumed_meds_today: string().oneOf(medsTakenTodayOptions.map(item => item.value)).required("Required"),
  intake_start_date: string().when('startDateOption', { is: undefined, then: (schema) => schema.required(), otherwise: (schema) => schema.optional() }),
  startDateOption: string().oneOf(startDateOptions.map(item => item.value)).optional(),
});

export type IntakeFormSchema = InferType<typeof schema>;

async function onSubmit(event: FormSubmitEvent<IntakeFormSchema>) {
  try {
    await props.submitCallback(event.data)
  } catch (error) {
    if (form.value && (isFetchError(error) || isNuxtError(error))) {
      let errors: FormError[] = [];
      if (isFastAPIPlausibilityError(error.data)) {
        errors = error.data.detail.fields.map(field => {
          return {
            path: field,
            message: plausibilityErrorMessages.find((value) => value.rule === error.data.detail.rule)?.message ?? error.data.detail.msg,
          }
        }) ?? [];
      } else if (isFastAPIValidationError(error.data) && error.data.detail) {
        errors = error.data.detail.filter(value => {
          return value.loc.every(value => typeof value === 'string') && value.loc.length === 2 && value.loc[0] === 'body';
        }).map(value => {
          return {
            path: value.loc[1] as string,
            message: value.msg,
          };
        })
      }
      if (errors.length === 0) {
        throw error;
      }
      form.value.setErrors(errors);
    } else {
      throw error;
    }
  }
}

watch(() => props.drugId, async (newDrugId?: string) => {
  state.drugId = newDrugId ?? "";
}, { immediate: true });

onMounted(async () => {
  if (props.initialState) {
    // Populate form state with given state
    for (const key of Object.keys(state)) {
      if (props.initialState[key]) {
        (state as Record<string, unknown>)[key] = props.initialState[key];
      }
    }

    if (Object.hasOwn(props.initialState, 'is_activeingredient_equivalent_choice') && Object.keys(props.initialState).length === 1) {
      // Exit before validation. This initial state does not represent a full record and was only used to set
      // the "active ingredient is equivalent" directly from the search results.
      return;
    }
  }
})
</script>

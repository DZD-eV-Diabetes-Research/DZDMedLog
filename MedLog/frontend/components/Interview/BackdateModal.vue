<script setup lang="ts">
import type { FormSubmitEvent } from "#ui/types";
import { boolean, date, type InferType, object, ref as yupRef } from "yup";
import { useDayjs } from "#dayjs";

const dayjs = useDayjs();

interface Props {
  submitCallback: (data: BackdateFormSchema) => Promise<void>;
}

const props = defineProps<Props>();

const modelValue = defineModel<boolean>();

const takenMedsOptions = [
  { label: "Ja", value: true },
  { label: "Nein", value: false },
]

const createError = ref();
const endDate = ref(dayjs(new Date()).format("YYYY-MM-DD"));
const endTime = ref(dayjs(new Date()).format("HH:mm"));
const startDate = ref(dayjs(new Date()).format("YYYY-MM-DD"));
const startTime = ref(dayjs(new Date()).format("HH:mm"));

const state = reactive<Partial<BackdateFormSchema>>({
  interview_start_time_utc: undefined,
  interview_end_time_utc: undefined,
  proband_has_taken_meds: undefined,
});

const schema = object({
  interview_start_time_utc: date()
      .max(new Date(), "Das Datum darf nicht in der Zukunft liegen")
      .required("Das Startdatum ist immer anzugeben"),
  interview_end_time_utc: date().when('proband_has_taken_meds', {
    is: false,
    then: schema => schema
        .min(yupRef('interview_start_time_utc'), "Das Ende darf nicht vor dem Beginn liegen")
        .max(new Date(), "Das Datum darf nicht in der Zukunft liegen")
        .required("Ohne zu erfassende Medikamente, wird das Interview direkt abgeschlossen. Bitte Zeitpunkt angeben."),
    otherwise: schema => schema.notRequired()
  }),
  proband_has_taken_meds: boolean().nonNullable().defined().required("Bitte treffen sie eine Auswahl"),
});

export type BackdateFormSchema = InferType<typeof schema>;

async function createInterview(event: FormSubmitEvent<BackdateFormSchema>) {
  try {
    await props.submitCallback({
      interview_start_time_utc: event.data.interview_start_time_utc,
      proband_has_taken_meds: event.data.proband_has_taken_meds,
      interview_end_time_utc: event.data.proband_has_taken_meds ? undefined : event.data.interview_end_time_utc,
    })
    // Close the modal
    modelValue.value = false;
  } catch (error) {
    createError.value = error;
  }
}

watch(() => state.proband_has_taken_meds, (newValue, oldValue) => {
  if (newValue === false && oldValue !== false) {
    endDate.value = startDate.value;
    endTime.value = startTime.value;
  }
});

watch([startDate, startTime], ([newStartDate, newStartTime]) => {
  state.interview_start_time_utc = dayjs(`${newStartDate} ${newStartTime}`).toDate();
}, { immediate: true })

watch([endDate, endTime], ([newEndDate, newEndTime]) => {
  state.interview_end_time_utc = dayjs(`${newEndDate} ${newEndTime}`).toDate();
}, { immediate: true })
</script>

<template>
  <DZDUIModal v-model="modelValue" title="Interview nachtragen" :error="createError" >
    <UForm :schema="schema" :state="state" class="space-y-4 mt-2" @submit="createInterview">
      <UFormGroup label="Beginn des Interviews" name="interview_start_time_utc" required>
        <div class="flex flex-row">
          <UInput v-model="startDate" type="date" required />
          <UInput v-model="startTime" type="time" class="ms-2" required />
        </div>
      </UFormGroup>
      <UFormGroup label="Wurden Medikamente eingenommen?" name="proband_has_taken_meds" required>
        <URadioGroup
            v-model="state.proband_has_taken_meds"
            :options="takenMedsOptions"
            name="proband_has_taken_meds"
        />
      </UFormGroup>
      <UFormGroup v-if="state.proband_has_taken_meds === false" label="Ende des Interviews" name="interview_end_time_utc" required>
        <div class="flex flex-row">
          <UInput v-model="endDate" type="date" required />
          <UInput v-model="endTime" type="time" class="ms-2" required />
        </div>
      </UFormGroup>
      <hr>
      <div class="flex justify-between">
        <UButton label="Abbrechen" color="gray" @click.prevent="modelValue = false" />
        <UButton type="submit" :label="state.proband_has_taken_meds ? 'Anlegen' : 'Anlegen und abschließen'" />
      </div>
    </UForm>
  </DZDUIModal>
</template>

<style scoped>

</style>

<script setup lang="ts">
import type { FormSubmitEvent } from "#ui/types";
import { date, object, ref as yupRef, string } from "yup";
import { useDayjs } from "#dayjs";
import type { SchemaInterview, SchemaInterviewUpdateApi } from "#open-fetch-schemas/medlogapi";

const dayjs = useDayjs();

interface Props {
  interview: SchemaInterview;
  eventTypeEditable: boolean;
  eventTypeOptions: { label: string; value: string }[];
  defaultEventType?: string | null;
  submitCallback: (body: SchemaInterviewUpdateApi) => Promise<void>;
}

const props = withDefaults(defineProps<Props>(), {
  defaultEventType: null,
});

const modelValue = defineModel<boolean>();

interface EditFormState {
  interview_start_time_utc?: Date;
  interview_end_time_utc?: Date;
  event_type?: string;
}

const patchError = ref();
const interviewEnded = !!props.interview.interview_end_time_utc;

const originalStart = dayjs.utc(props.interview.interview_start_time_utc).toDate();
const originalEnd = interviewEnded ? dayjs.utc(props.interview.interview_end_time_utc).toDate() : undefined;

const initialStart = toInputValues(originalStart);
const initialEnd = originalEnd ? toInputValues(originalEnd) : undefined;

const startDate = ref(initialStart.date);
const startTime = ref(initialStart.time);
const endDate = ref(initialEnd?.date ?? "");
const endTime = ref(initialEnd?.time ?? "");

const state = reactive<EditFormState>({
  interview_start_time_utc: undefined,
  interview_end_time_utc: undefined,
  // Pre-fill a missing type with the event's type ("fixed" or "default")
  event_type: props.interview.event_type ?? props.defaultEventType ?? "",
});

// "now" is evaluated on validation, so a long open dialog does not reject valid times
function notInFuture(value: Date | null | undefined) {
  return !value || value <= new Date();
}

const futureMessage = "Das Datum darf nicht in der Zukunft liegen";

const schema = object({
  interview_start_time_utc: date()
      .test("not-in-future", futureMessage, notInFuture)
      .required("Das Startdatum ist immer anzugeben"),
  interview_end_time_utc: interviewEnded
      ? date()
          .min(yupRef("interview_start_time_utc"), "Das Ende darf nicht vor dem Beginn liegen")
          .test("not-in-future", futureMessage, notInFuture)
          .required("Das Ende eines abgeschlossenen Interviews ist immer anzugeben")
      : date().notRequired(),
  event_type: props.eventTypeEditable
      ? string().required("Bitte Erhebungsmodus wählen")
      : string().notRequired(),
});

function toInputValues(value: Date) {
  const local = dayjs(value);
  return { date: local.format("YYYY-MM-DD"), time: local.format("HH:mm") };
}

// The inputs only have minute precision, so an unchanged time keeps its stored value (incl. seconds)
function toDate(newDate: string, newTime: string, initial: { date: string; time: string } | undefined, original: Date | undefined) {
  if (!newDate || !newTime) {
    return undefined;
  }
  if (initial && newDate === initial.date && newTime === initial.time) {
    return original;
  }
  return dayjs(`${newDate} ${newTime}`).toDate();
}

async function submitForm(event: FormSubmitEvent<EditFormState>) {
  const body: SchemaInterviewUpdateApi = {};
  const start = event.data.interview_start_time_utc;
  const end = event.data.interview_end_time_utc;

  if (start && start.getTime() !== originalStart.getTime()) {
    // include start datetime, if changed
    body.interview_start_time_utc = start.toISOString();
  }
  if (interviewEnded && end && end.getTime() !== originalEnd?.getTime()) {
    // include end datetime, if changed
    body.interview_end_time_utc = end.toISOString();
  }
  if (props.eventTypeEditable && event.data.event_type && event.data.event_type !== props.interview.event_type) {
    // include event type, if enabled and changed
    body.event_type = event.data.event_type;
  }

  try {
    if (Object.keys(body).length) {
      await props.submitCallback(body);
    }
    modelValue.value = false;  // Close the modal
  } catch (error) {
    patchError.value = error;
  }
}

watch([startDate, startTime], ([newStartDate, newStartTime]) => {
  state.interview_start_time_utc = toDate(newStartDate, newStartTime, initialStart, originalStart);
}, { immediate: true })

watch([endDate, endTime], ([newEndDate, newEndTime]) => {
  state.interview_end_time_utc = interviewEnded ? toDate(newEndDate, newEndTime, initialEnd, originalEnd) : undefined;
}, { immediate: true })
</script>

<template>
  <DZDUIModal v-model="modelValue" title="Interview bearbeiten" :error="patchError">
    <UForm :schema="schema" :state="state" class="space-y-4 mt-2" @submit="submitForm">
      <UFormGroup label="Beginn des Interviews" name="interview_start_time_utc" required>
        <div class="flex flex-row">
          <UInput v-model="startDate" type="date" required />
          <UInput v-model="startTime" type="time" class="ms-2" required />
        </div>
      </UFormGroup>
      <UFormGroup v-if="interviewEnded" label="Ende des Interviews" name="interview_end_time_utc" required>
        <div class="flex flex-row">
          <UInput v-model="endDate" type="date" required />
          <UInput v-model="endTime" type="time" class="ms-2" required />
        </div>
      </UFormGroup>
      <UFormGroup v-if="eventTypeEditable" label="Erhebungsmodus" name="event_type" required>
        <USelect
            v-model="state.event_type"
            :options="eventTypeOptions"
            placeholder="Erhebungsmodus wählen ..."
        />
      </UFormGroup>
      <hr>
      <div class="flex justify-between">
        <UButton label="Abbrechen" color="gray" @click.prevent="modelValue = false" />
        <UButton type="submit" label="Speichern" />
      </div>
    </UForm>
  </DZDUIModal>
</template>

<style scoped>

</style>

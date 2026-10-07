<script setup lang="ts">
import type { FormSubmitEvent } from "#ui/types";
import { date, type InferType, object } from "yup";
import { useDayjs } from "#dayjs";

const dayjs = useDayjs();

interface Props {
  startDate: Date;
  submitCallback: (data: CustomEndFormSchema) => Promise<void>;
}

const props = defineProps<Props>();

const modelValue = defineModel<boolean>();

const patchError = ref();
const endDate = ref(dayjs(new Date()).format("YYYY-MM-DD"));
const endTime = ref(dayjs(new Date()).format("HH:mm"));

const state = reactive<Partial<CustomEndFormSchema>>({
  interview_end_time_utc: undefined,
});

const schema = object({
  interview_end_time_utc: date()
      .min(props.startDate, "Das Ende darf nicht vor dem Beginn liegen")
      .max(new Date(), "Das Datum darf nicht in der Zukunft liegen")
      .required("Das Datum muss angegeben werden"),
});

export type CustomEndFormSchema = InferType<typeof schema>;

async function submitForm(event: FormSubmitEvent<CustomEndFormSchema>) {
  try {
    await props.submitCallback(event.data)
    modelValue.value = false;  // Close the modal
  } catch (error) {
    patchError.value = error;
  }
}

watch([endDate, endTime], ([newEndDate, newEndTime]) => {
  state.interview_end_time_utc = dayjs(`${newEndDate} ${newEndTime}`).toDate();
}, { immediate: true })
</script>

<template>
  <DZDUIModal v-model="modelValue" title="Interview nachträglich abschließen" :error="patchError" >
    <UForm :schema="schema" :state="state" class="space-y-4 mt-2" @submit="submitForm">
      <UFormGroup label="Ende des Interviews" name="interview_end_time_utc" required>
        <div class="flex flex-row">
          <UInput v-model="endDate" type="date" required />
          <UInput v-model="endTime" type="time" class="ms-2" required />
        </div>
      </UFormGroup>
      <hr>
      <div class="flex justify-between">
        <UButton label="Abbrechen" color="gray" @click.prevent="modelValue = false" />
        <UButton type="submit" color="red" label="Abschließen" />
      </div>
    </UForm>
  </DZDUIModal>
</template>

<style scoped>

</style>

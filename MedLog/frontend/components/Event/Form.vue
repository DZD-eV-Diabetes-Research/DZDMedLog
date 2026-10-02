<script setup lang="ts">
import { type InferType, object, string } from "yup";
import type {FormSubmitEvent} from "#ui/types";

const props = defineProps<{
  submitCallback: (data: EventFormSchema) => Promise<void>;
}>();

defineEmits(['cancel'])

const eventState = reactive({ name: "" });

const eventSchema = object({
  name: string().required("Das Event muss einen Namen haben"),
});

export type EventFormSchema = InferType<typeof eventSchema>;

async function onSubmit(event: FormSubmitEvent<EventFormSchema>) {
  await props.submitCallback(event.data);
}
</script>

<template>
  <UForm :schema="eventSchema" :state="eventState" class="space-y-4" @submit="onSubmit">
    <UFormGroup label="Name des Events" description="Der Name muss innerhalb der Studie eindeutig sein." name="name">
      <UInput v-model="eventState.name" required placeholder="Interview Nr. 1" />
    </UFormGroup>
    <hr>
    <div class="flex justify-between">
      <UButton label="Abbrechen" variant="outline" @click.prevent="$emit('cancel')" />
      <UButton type="submit" label="Event anlegen" />
    </div>
  </UForm>
</template>

<style scoped>

</style>

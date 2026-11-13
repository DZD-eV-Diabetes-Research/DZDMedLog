<script setup lang="ts">
import { type InferType, object, string } from "yup";
import type {FormSubmitEvent} from "#ui/types";
import type { SchemaEventTypeMode } from "#open-fetch-schemas/medlogapi";
import { eventTypeModeOptions } from "~/constants";

const props = defineProps<{
  initialState?: Partial<EventFormSchema>;
  submitCallback: (data: EventFormSchema) => Promise<void>;
}>();

defineEmits(['cancel'])

const configStore = useConfigStore();

// A type removed from the server config after the event got it stays selectable for this event
const eventTypeOptions = computed(() => {
  const options = [...configStore.eventTypeOptions];
  const currentType = props.initialState?.event_type;
  if (currentType && !configStore.eventTypes.eventTypes.includes(currentType)) {
    options.push({ label: `${currentType} (nicht mehr konfiguriert)`, value: currentType });
  }
  return options;
});

// USelect only emits strings, so "" stands for "not set" while editing
const eventState = reactive({
  name: "",
  external_id: "",
  event_type_mode: "" as SchemaEventTypeMode | "",
  event_type: "",
});

// The API expects `null` for "not set"
const emptyToNull = (value: string | null) => value?.trim() || null;

const eventSchema = computed(() => object({
  name: string().required("Das Event muss einen Namen haben"),
  external_id: string().nullable().defined().transform(emptyToNull)
      .max(128, "Die externe ID darf maximal 128 Zeichen lang sein"),
  event_type_mode: string().nullable().defined().transform(emptyToNull)
      .oneOf(eventTypeModeOptions.map(option => option.value).filter(value => value !== "")),
  event_type: string().nullable().defined().transform(emptyToNull).when("event_type_mode", {
    is: (mode: string | null) => mode === "fixed" || mode === "default",
    then: schema => schema
        .required("Hierfür muss ein Erhebungsmodus gewählt werden")
        .oneOf(eventTypeOptions.value.map(option => option.value), "Dieser Erhebungsmodus ist auf dem Server nicht konfiguriert"),
  }),
}));

export type EventFormSchema = InferType<typeof eventSchema.value>;

const modeNeedsEventType = computed(() => {
  return eventState.event_type_mode === "fixed" || eventState.event_type_mode === "default";
});

async function onSubmit(event: FormSubmitEvent<EventFormSchema>) {
  await props.submitCallback(event.data);
}

watch(modeNeedsEventType, (needsEventType) => {
  if (!needsEventType) {
    eventState.event_type = "";
  }
});

onMounted(async () => {
  if (props.initialState) {
    // Populate form state with given state
    for (const key of Object.keys(eventState) as (keyof typeof eventState)[]) {
      const value = props.initialState[key];
      if (value !== undefined && value !== null) {
        (eventState as Record<string, unknown>)[key] = value;
      }
    }
  }
})
</script>

<template>
  <UForm :schema="eventSchema" :state="eventState" class="space-y-4" @submit="onSubmit">
    <UFormGroup label="Name des Events" description="Der Name muss innerhalb der Studie eindeutig sein." name="name">
      <UInput v-model="eventState.name" required placeholder="Interview Nr. 1" />
    </UFormGroup>
    <UFormGroup label="Externe ID" description="Optional, z.B. die ID des Events im eCRF. Dient nur der Zuordnung im Export." name="external_id">
      <UInput v-model="eventState.external_id" />
    </UFormGroup>
    <template v-if="configStore.eventTypes.enabled">
      <UFormGroup label="Erhebungsmodus erfassen" description="Ob und wie der Erhebungsmodus (z.B. vor Ort oder remote) der Interviews dieses Events festgelegt wird." name="event_type_mode">
        <USelect v-model="eventState.event_type_mode" :options="eventTypeModeOptions" />
      </UFormGroup>
      <UFormGroup v-if="modeNeedsEventType" label="Erhebungsmodus" name="event_type" required>
        <USelect v-model="eventState.event_type" :options="eventTypeOptions" placeholder="Erhebungsmodus wählen ..." />
      </UFormGroup>
    </template>
    <hr>
    <div class="flex justify-between">
      <UButton label="Abbrechen" variant="outline" @click.prevent="$emit('cancel')" />
      <UButton type="submit" :label="initialState ? 'Event speichern' : 'Event anlegen'" />
    </div>
  </UForm>
</template>

<style scoped>

</style>

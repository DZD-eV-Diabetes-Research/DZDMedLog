<script setup lang="ts">
import { onMounted, reactive } from "#imports";
import {boolean, type InferType, object, string} from "yup";
import type { FormSubmitEvent } from "#ui/types";
import type { SchemaStudy } from "#open-fetch-schemas/medlogapi";

const props = defineProps<{
  initialState?: SchemaStudy;
}>();

const emit = defineEmits(['cancel', 'save']);

const state = reactive<StudyFormSchema>({
  display_name: "",
  no_permissions: false,
  deactivated: false,
});

const schema = object({
  display_name: string().max(128).required("Ein Name ist erforderlich"),
  no_permissions: boolean().required(),
  deactivated: boolean().required(),
});

export type StudyFormSchema = InferType<typeof schema>;

async function onSubmit(event: FormSubmitEvent<StudyFormSchema>) {
  emit('save', event.data);
}

onMounted(async () => {
  if (props.initialState) {
    // Populate form state with given state
    for (const key of Object.keys(state) as Array<keyof typeof state>) {
      if (props.initialState[key] !== undefined) {
        (state as Record<string, unknown>)[key] = props.initialState[key];
      }
    }
  }
})
</script>

<template>
  <UForm :state="state" :schema="schema" class="space-y-4" @submit="onSubmit">
    <UFormGroup label="Name" name="display_name">
      <UInput v-model="state.display_name" type="text" />
    </UFormGroup>

    <UFormGroup
        label="Vereinfachtes Rechtekonzept"
        name="no_permissions"
        description="Eingeloggte Nutzende benötigen keine gesonderte Freigabe für die Studie, um Interviews zu führen. Adminrechte müssen weiterhin explizit vergeben werden."
    >
      <UToggle v-model="state.no_permissions" />
    </UFormGroup>

    <UFormGroup
        label="Deaktiviert"
        name="deactivated"
    >
      <template #description>
        Versteckt die Studie außerhalb der Studienverwaltung.
        <span class="text-red-500">Kann derzeit nicht rückgängig gemacht werden!</span>
      </template>

      <UToggle v-model="state.deactivated" />
    </UFormGroup>
    <hr>
    <div class="flex justify-between">
      <UButton label="Abbrechen" variant="outline" @click.prevent="$emit('cancel')" />
      <UButton type="submit" label="Speichern" />
    </div>
  </UForm>
</template>

<style scoped>

</style>

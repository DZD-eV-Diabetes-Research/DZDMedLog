<script setup lang="ts">
import { boolean, type InferType, object, string } from "yup";
import type { FormSubmitEvent } from "#ui/types";

const props = defineProps<{
  initialState?: any;
}>();

const emit = defineEmits(['cancel', 'save']);

const studyForm = useTemplateRef('study-form');

const state = reactive({
  display_name: "",
  no_permissions: false,
  deactivated: false,
});

const schema = object({
  display_name: string().required("Ein Name ist erforderlich"),
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
    for (const key of Object.keys(state)) {
      if (props.initialState[key]) {
        state[key] = props.initialState[key];
      }
    }

    try {
      await studyForm.value.validate();
    } catch (error) { // eslint-disable-line @typescript-eslint/no-unused-vars
      // Swallow error, the result is shown directly in the form
    }
  }
})
</script>

<template>
  <UForm ref="study-form" :state="state" :schema="schema" class="space-y-4" @submit="onSubmit">
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

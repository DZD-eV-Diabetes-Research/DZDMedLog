<script setup lang="ts">
import { onMounted, reactive } from "#imports";
import {boolean, type InferType, object, string} from "yup";
import type { FormSubmitEvent } from "#ui/types";
import type { SchemaProbandExternalIdNormalization, SchemaStudy } from "#open-fetch-schemas/medlogapi";
import { probandExternalIdNormalizationOptions } from "~/constants";
import { StudyManagementRegExCheckModal } from "#components";

const modal = useModal();

const props = defineProps<{
  initialState?: SchemaStudy;
}>();

const emit = defineEmits<{
  cancel: []
  save: [data: StudyFormSchema]
}>();

const state = reactive<StudyFormSchema>({
  display_name: "",
  no_permissions: false,
  deactivated: false,
  proband_external_id_pattern: "",
  proband_external_id_pattern_error_text: "",
  proband_external_id_normalization: "none",
  proband_external_id_example: "",
});

const schema = object({
  display_name: string().max(128).required("Ein Name ist erforderlich"),
  no_permissions: boolean().required(),
  deactivated: boolean().required(),
  proband_external_id_pattern: string().max(1024).nullable(),
  proband_external_id_pattern_error_text: string().max(1024).nullable(),
  proband_external_id_normalization: string().oneOf(probandExternalIdNormalizationOptions.map(item => item.value)),
  proband_external_id_example: string().max(1024).nullable(),
});

export type StudyFormSchema = InferType<typeof schema>;

async function onSubmit(event: FormSubmitEvent<StudyFormSchema>) {
  emit('save', event.data);
}

function openRegExCheckModal() {
  modal.open(StudyManagementRegExCheckModal, {
    async onCancel()  {
      await modal.close()
    },
    async onConfirm(newPattern: string, newNormalization: SchemaProbandExternalIdNormalization) {
      await modal.close();
      state.proband_external_id_pattern = newPattern;
      state.proband_external_id_normalization = newNormalization;
    },
    pattern: state.proband_external_id_pattern ?? '',
    normalization: state.proband_external_id_normalization,
  })
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
    <UCard
        class="border border-gray-400"
        :ui="{
            header: {
              padding: 'pt-5 pb-2'
            },
            divide: '',
            body: {
              padding: 'py-4 sm:p-4 sm:px-6'
            },
          }"
    >
      <template #header>
        <h2 class="text-xl">Grundeinstellungen</h2>
      </template>

      <UFormGroup
          label="Name"
          name="display_name"
          description="Der Name der Studie."
          required
      >
        <UInput v-model="state.display_name" type="text" />
      </UFormGroup>
    </UCard>

    <UCard
        class="border border-gray-400"
        :ui="{
            header: {
              padding: 'pt-5 pb-2'
            },
            divide: '',
            body: {
              padding: 'py-4 sm:p-4 sm:px-6'
            },
          }"
    >
      <template #header>
        <div class="flex flex-row justify-between">
          <h2 class="text-xl">Probanden-IDs</h2>
          <UButton color="gray" variant="outline" icon="i-heroicons-beaker-solid" @click.prevent="openRegExCheckModal()">
            Normalisierung & Regulären Ausdruck testen
          </UButton>
        </div>
      </template>

      <div class="space-y-4">
        <UFormGroup
            label="Normalisierung"
            name="proband_external_id_normalization"
            description="Kann verwendet werden, um Probanden-IDs vor Beginn des Interviews zu vereinheitlichen. Dies vermeidet unbeabsichtigte Zusammenlegung oder Aufteilung von Probanden durch unterschiedliche Schreibweisen."
        >
          <USelect v-model="state.proband_external_id_normalization" :options="probandExternalIdNormalizationOptions" />
        </UFormGroup>

        <UFormGroup
            label="Regulärer Ausdruck"
            name="proband_external_id_pattern"
            description="Optionaler regulärer Ausdruck, gegen den eine Probanden-ID nach der Normalisierung geprüft wird. Leer lassen, um beliebige Probanden-IDs zuzulassen."
        >
          <UInput :model-value="state.proband_external_id_pattern ?? ''" type="text" @update:model-value="value => state.proband_external_id_pattern = String(value).trim()" />
        </UFormGroup>

        <UFormGroup
            label="Fehlertext"
            name="proband_external_id_pattern_error_text"
            description="Dieser optionale Text wird angezeigt, wenn die ID nach der Normalisierung nicht dem Muster entspricht."
        >
          <UInput :model-value="state.proband_external_id_pattern_error_text ?? ''" type="text" @update:model-value="value => state.proband_external_id_pattern_error_text = value" />
        </UFormGroup>

        <UFormGroup
            label="Beispiel-ID"
            name="proband_external_id_example"
            description="Optionales Positivbeispiel für eine Probanden-ID, die neben der Eingabe gezeigt werden kann."
        >
          <UInput :model-value="state.proband_external_id_example ?? ''" type="text" @update:model-value="value => state.proband_external_id_example = value" />
        </UFormGroup>
      </div>
    </UCard>

    <UCard
        class="bg-red-50 border-red-400 border"
        :ui="{
            header: {
              padding: 'pt-5 pb-2'
            },
            divide: '',
            body: {
              padding: 'py-4 sm:p-4 sm:px-6'
            },
          }"
    >
      <template #header>
        <h2 class="text-xl">Danger Zone</h2>
      </template>

      <div class="space-y-4">
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
      </div>
    </UCard>
    <hr>
    <div class="flex justify-between">
      <UButton label="Abbrechen" variant="outline" @click.prevent="$emit('cancel')" />
      <UButton type="submit" label="Speichern" />
    </div>
  </UForm>
</template>

<style scoped>

</style>

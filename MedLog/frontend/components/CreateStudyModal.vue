<script setup lang="ts">
import { object, string } from "yup";

const studyStore = useStudyStore();

const modelValue = defineModel<boolean>();

const emit = defineEmits<{
  createStudy: [name: string, cloneFromId?: string];
}>();

const items = [
  {
    label: 'Studienstruktur übernehmen',
    icon: 'i-heroicons-document-duplicate',
    defaultOpen: false,
    slot: 'clone-study'
  },
];

const availableStudiesOptions = computed(() => {
  const options: {
    label: string;
    value?: string;
  }[] = [{ label: 'Keine Auswahl', value: "" }];
  return options.concat(studyStore.allStudies
      .map(study => {
        return {
          label: study.display_name ?? 'N/A',
          value: study.id,
        };
      })
      .sort((a, b) => a.label.localeCompare(b.label))
  );
});

const state = reactive({
  studyName: "",
  studyIdToClone: "",
});

const schema = object({
  studyName: string().max(128, "Der Name kann maximal 128 Zeichen lang sein").required("Bitte geben Sie den Namen der Studie an"),
  studyIdToClone: string().optional(),
});

function onClose() {
  modelValue.value = false;
}

function createStudy() {
  emit("createStudy", state.studyName.trim(), state.studyIdToClone);
}

watch(modelValue, (isOpen) => {
  // Reset form state on visibility change
  if (isOpen) {
    state.studyName = "";
  }
})
</script>

<template>
  <UModal v-model="modelValue" prevent-close>
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-lg">Studie anlegen</span>
          <UButton color="gray" variant="ghost" icon="i-heroicons-x-mark-20-solid" class="-my-1" @click="onClose" />
        </div>
      </template>

      <slot name="error" />

      <UForm :schema="schema" :state="state" class="space-y-4 mt-2" @submit="createStudy">
        <UFormGroup label="Name der Studie" name="studyName" required>
          <UInput v-model="state.studyName" autofocus required />
        </UFormGroup>

        <UAccordion :items="items" color="gray" variant="solid">
          <template #clone-study>
            <div class="px-4">
              <p class="mb-2">
                Optional kann die Struktur einer anderen Studie übernommen werden.
                Dies umfasst Einstellungen zur Probanden-ID, die Einstellung zum vereinfachten Rechtekonzept sowie Namen und Reihenfolge der Events.
                Es werden keine Daten oder individuellen Berechtigungen übernommen.
              </p>
              <UFormGroup label="Struktur dieser Studie übernehmen" name="studyIdToClone">
                <USelectMenu
                    v-model="state.studyIdToClone"
                    :options="availableStudiesOptions"
                    placeholder="Studie auswählen"
                    value-attribute="value"
                    option-attribute="label"
                    :searchable="true"
                />
              </UFormGroup>
            </div>
          </template>
        </UAccordion>

        <div class="flex justify-between">
          <UButton label="Abbrechen" color="gray" variant="outline" @click.prevent="onClose" />
          <UButton type="submit" label="Studie anlegen" />
        </div>
      </UForm>
    </UCard>
  </UModal>
</template>

<style scoped>

</style>

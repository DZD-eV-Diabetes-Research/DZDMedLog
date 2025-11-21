<template>
  <UModal>
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-lg">Präparat erfassen</span>
          <UButton color="gray" variant="ghost" icon="i-heroicons-x-mark-20-solid" class="-my-1" @click="$emit('cancel')" />
        </div>
      </template>

      <div v-if="!intakeDrugId">
        <p class="text-base mb-2">
          Präparat aus der Datenbank auswählen
        </p>
        <DrugSearch :autofocus-input="true" @drug-selected="onDrugSelected" />

        <UDivider label="oder" class="my-4" />

        <p>
          Falls ein Präparat nicht in der Datenbank enthalten ist, kann es hier hinzugefügt werden.
          Danach ist es über die Suche auffindbar.
        </p>
        <div class="flex justify-end">
          <UButton
              label="Ungelistetes Medikament aufnehmen" color="yellow" variant="outline"
              @click="openCustomModal()"
          />
        </div>
      </div>

      <div v-else>
        <DrugSummaryCard v-model="intakeDrugId" :readonly="!isDrugEditable" class="mb-4" />
        <IntakeForm
            :drug-id="intakeDrugId"
            :initial-state="props.initialState"
            @cancel="$emit('cancel')"
            @save="data => $emit('save', data)"
        />
      </div>
    </UCard>

    <UModal v-model="customDrugModalVisibility" prevent-close>
      <UCard>
        <template #header>
          Präparat anlegen
        </template>

        <UAlert
            icon="i-heroicons-information-circle"
            color="sky"
            variant="subtle"
            description="Der Name des Präparats ist das einzige Pflichtfeld. Sollten Codes (z.B. PZN) bekannt sein, können diese bei einer späteren Datenharmonisierung helfen."
        />
        <CustomDrugForm
            class="mt-5"
            @save="saveCustomDrug"
            @cancel="customDrugModalVisibility = false"
        />
        <ErrorMessage
            v-if="createCustomDrugError"
            title="Konnte Präparat nicht speichern"
            :error="createCustomDrugError"
            class="mt-5"
        />
      </UCard>
    </UModal>
  </UModal>
</template>

<script setup lang="ts">
import type { DrugBody } from "~/components/CustomDrugForm.vue";

const props = defineProps({
  isDrugEditable: { type: Boolean, default: true },
  initialState: { type: Object, default: null },
});

defineEmits(['cancel', 'save'])

const createCustomDrugError = ref();
const customDrugModalVisibility = ref(false);
const intakeDrugId = ref<string>('');

function onDrugSelected(newDrugId) {
  intakeDrugId.value = newDrugId;
}

async function openCustomModal() {
  customDrugModalVisibility.value = true
}

async function saveCustomDrug(customDrugBody: DrugBody) {
  createCustomDrugError.value = undefined;
  const { data, error } = await useMedlogapi(
      `/api/drug/custom`,
      {
        method: "POST",
        body: customDrugBody
      }
  );

  if (error.value) {
    createCustomDrugError.value = error.value;
    return;
  }

  if (data.value?.id) {
    intakeDrugId.value = data.value?.id;
  }

  customDrugModalVisibility.value = false;
}

onMounted(async () => {
  if (props.initialState?.drugId) {
    // Populate selected drug from given state
    intakeDrugId.value = props.initialState.drugId;
  }
})
</script>

<style scoped>

</style>

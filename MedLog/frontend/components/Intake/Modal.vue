<template>
  <UModal>
    <div v-if="!intakeDrugId" class="p-4">
      <DrugSearch
          @drug-selected="drugId => intakeDrugId = drugId"
      />
      <UButton
          label="Ungelistetes Medikament aufnehmen" color="yellow" variant="soft"
          class="border border-yellow-500 hover:bg-yellow-300 hover:border-white hover:text-white mt-4"
          @click="openCustomModal()"
      />
    </div>
    <div v-else class="p-4">
      <DrugSummaryCard v-model="intakeDrugId" :readonly="!isDrugEditable" />
    </div>
    <hr>
    <div class="p-4">
      <IntakeForm
          :drug-id="intakeDrugId"
          :initial-state="props.initialState"
          @cancel="$emit('cancel')"
          @save="data => $emit('save', data)"
      />
    </div>
    <UModal v-model="customDrugModalVisibility">
      <UCard>
        <template #header>
          Medikament anlegen
        </template>

        <UAlert
            icon="i-heroicons-information-circle"
            color="sky"
            variant="subtle"
            description="Legen Sie hier ein Medikament an, das nicht in der Medikamentendatenbank enthalten ist.
                Es kann danach über die Suche gefunden werden."
        />
        <CustomDrugForm
            class="mt-5"
            :error="createCustomDrugError"
            @save="saveCustomDrug"
            @cancel="customDrugModalVisibility = false"
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

const intakeDrugId = ref<string>('');

const createCustomDrugError = ref("");
const customDrugModalVisibility = ref(false);

async function openCustomModal() {
  customDrugModalVisibility.value = true
}

async function saveCustomDrug(customDrugBody: DrugBody) {
  createCustomDrugError.value = "";
  const { error } = await useMedlogapi(
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

  // TODO select newly created drug in the form

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

<template>
  <USkeleton v-if="loading"/>
  <UAlert v-else-if="errorMessage" color="red" title="Fehler beim Laden des Medikaments" :description="errorMessage"/>
  <UAlert v-else :actions="actions" :title="title" class="bg-blue-100">
    <template #description>
      <div v-if="keyValuePills" class="flex flex-row">
        <KeyValuePill
            v-for="{ label, value } in keyValuePills"
            :key="label"
            :key-label="label"
            :value-label="value"
            class="mr-2"
        />
      </div>
    </template>
  </UAlert>
</template>

<script setup lang="ts">
const model = defineModel({ type: String, required: true });

const props = defineProps({
  readonly: { type: Boolean, default: false },
});

const actions = computed(() => {
  if (props.readonly) {
    return [];
  }

  return [{ label: 'Präparat ändern', variant: 'outline', color: 'gray', click: () => model.value = '' }];
});
const keyValuePills = computed(() =>  {
  const pills = [];

  for (const key of Object.keys(codes.value)) {
    pills.push({ label: key, value: codes.value[key] });
  }

  // Only include entries with a value
  return pills.filter(item => item.value);
});

const loading = ref<boolean>(false);
const errorMessage = ref<string>('');
const title = ref<string>('');
const codes = ref<Record<string, string>>({});

async function loadDrug(drugId) {
  loading.value = true;
  errorMessage.value = '';
  const { data, error } = await useMedlogapi('/api/drug/id/{drug_id}', {
    path: {
      drug_id: drugId,
    }
  })

  if (error.value) {
    errorMessage.value = error.value.message ?? error.value ?? 'Unbekannter Fehler';
    loading.value = false;
    return;
  }

  title.value = data.value.trade_name ?? 'Kein Name';
  codes.value = data.value.codes ?? {};

  loading.value = false;
}

watch(() => model.value, async (newDrugId: string) => {
  await loadDrug(newDrugId)
}, { immediate: true });
</script>

<style scoped>

</style>

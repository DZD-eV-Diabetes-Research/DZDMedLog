<script setup lang="ts">
import type { SchemaIntakeDetailListItem } from "#open-fetch-schemas/medlogapi";

const props = defineProps({
  canDelete: { type: Boolean, default: false },
  canEdit: { type: Boolean, default: false },
  intakes: {
    type: Array as () => SchemaIntakeDetailListItem[],
    required: true,
  },
  showEvent: { type: Boolean, default: false },
  title: { type: String, default: "Eingenommene Medikamente" },
});

defineEmits<{
  'edit-intake': [intakeId: string]
  'delete-intake': [row: object]
}>();

const itemsPerPage = 10

const page = ref(1)
const tableFilterString = ref('')

const filteredRows = computed(() => {
  if (!tableFilterString.value) {
    return props.intakes
  }

  return props.intakes.filter((intake) => {
    const codes = [];
    for (const codesKey in intake.drug.codes) {
      if (intake.drug.codes[codesKey as keyof typeof intake.drug.codes]) {
        codes.push(intake.drug.codes[codesKey as keyof typeof intake.drug.codes]);
      }
    }

    return [intake.drug.trade_name, ...codes].some((value) => {
      return String(value).toLowerCase().includes(tableFilterString.value.toLowerCase())
    })
  })
})

const rows = computed(() => {
  const data = tableFilterString.value ? filteredRows.value : props.intakes;
  return data.slice((page.value - 1) * itemsPerPage, page.value * itemsPerPage);
})
</script>

<template>
  <UCard :ui="{ body: { padding: 'py-4 sm:px-0' } }">
    <template #header>
      <div class="flex flex-col">
        <h2 class="text-lg self-center">{{ title }}</h2>
        <div class="flex flex-row justify-between">
          <UFormGroup label="Tabelle filtern">
            <template #description>
              Es werden Namen und Codes durchsucht
            </template>

            <UInput
                v-model="tableFilterString"
                name="tableFilterString"
                placeholder="Suchbegriff eingeben"
                icon="i-heroicons-magnifying-glass-20-solid"
                autocomplete="off"
                :ui="{ icon: { trailing: { pointer: '' } } }"
            >
              <template #trailing>
                <UButton
                    v-show="tableFilterString !== ''"
                    color="gray"
                    variant="link"
                    icon="i-heroicons-x-mark-20-solid"
                    :padded="false"
                    @click="tableFilterString = ''"
                />
              </template>
            </UInput>
          </UFormGroup>
        </div>
      </div>
    </template>

    <div class="flex flex-col gap-4">
      <IntakeTable
          :intakes="rows"
          :can-edit="canEdit"
          :can-delete="canDelete"
          :show-event="showEvent"
          @edit="(intakeId: string) => $emit('edit-intake', intakeId)"
          @delete="(row: object) => $emit('delete-intake', row)"
      />

      <UPagination
          v-if="intakes.length >= itemsPerPage || filteredRows.length >= itemsPerPage"
          v-model="page"
          :page-count="itemsPerPage"
          :total="filteredRows.length"
          class="self-center"
      />
    </div>
  </UCard>
</template>

<style scoped>

</style>

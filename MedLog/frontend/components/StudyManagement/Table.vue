<script setup lang="ts">
import type { SchemaStudy } from '#open-fetch-schemas/medlogapi'

const columns = [{
  key: 'display_name',
  label: 'Name',
  sortable: true,
  rowClass: 'max-w-64 break-all',
}, {
  key: 'active',
  label: 'Aktiv'
}, {
  key: 'protection',
  label: 'Rechtekonzept'
}, {
  key: 'actions'
}]

defineProps({
  loading: { type: Boolean, default: false },
  studies: { type: Array as () => SchemaStudy[], default: () => [] },
});

const sort = ref({
  column: 'display_name',
  direction: 'asc'
})
</script>

<template>
  <UTable :rows="studies" :columns="columns" :loading="loading" :sort="sort">
    <template #active-data="{ row }">
      <UIcon
          :name="row.deactivated ? 'i-heroicons-x-circle-solid' : 'i-heroicons-check-circle-solid'"
          class="text-xl"
          :class="row.deactivated ? 'text-red-500' : 'text-green-500'"
      />
    </template>

    <template #protection-data="{ row }">
      <UIcon
          :name="row.no_permissions ? 'i-heroicons-lock-open-solid' : 'i-heroicons-lock-closed-solid'"
          :title="row.no_permissions ? 'Interviews können von allen angemeldeten Nutzenden durchgeführt werden' : 'Jeglicher Zugriff muss geregelt werden'"
          class="text-xl"
      />
    </template>

    <template #actions-data="{ row }">
      <UButton
          :to="`/manage/studies/${row.id}`"
          label="Bearbeiten"
          icon="i-heroicons-pencil"
          variant="outline"
          color="gray"
          class="mr-2"
          :disabled="row.deactivated"
      />
      <UButton
          :to="`/manage/studies/${row.id}/events`"
          label="Events verwalten"
          icon="i-heroicons-calendar-days"
          variant="outline"
          color="gray"
          class="mr-2"
          :disabled="row.deactivated"
      />
      <UButton
          :to="`/manage/studies/${row.id}/access`"
          label="Zugriff bearbeiten"
          icon="i-heroicons-key-solid"
          variant="outline"
          color="gray"
          class="mr-2"
          :disabled="row.deactivated"
      />
      <UButton
          :to="`/studies/${row.id}/export`"
          label="Datenexport"
          icon="i-heroicons-cloud-arrow-down"
          variant="outline"
          color="gray"
          :disabled="row.deactivated"
      />
    </template>
  </UTable>
</template>

<style scoped>
:deep(td:first-child) {
  /* Override the white-space breaking for the first column  */
  white-space: unset;
}
</style>

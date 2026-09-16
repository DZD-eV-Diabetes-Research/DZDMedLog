<script setup lang="ts">
import type { SchemaStudyApiRead } from '#open-fetch-schemas/medlogapi'

const configStore = useConfigStore()
const studyPermissionStore = useStudyPermissionStore()

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
  studies: { type: Array as () => SchemaStudyApiRead[], default: () => [] },
});

const sort = ref<{
  column: string;
  direction: "asc" | "desc";
}>({
  column: 'display_name',
  direction: 'asc'
})

function isStudyAccessManaged(study: SchemaStudyApiRead) {
  return configStore.branding.disableUiPermissionManagement === true || study.is_oidc_permission_managed === true
}
</script>

<template>
  <UTable :rows="studies" :columns="columns" :loading="loading" :sort="sort">
    <template #active-data="{ row } : { row: SchemaStudyApiRead }">
      <UIcon
          :name="row.deactivated ? 'i-heroicons-x-circle-solid' : 'i-heroicons-check-circle-solid'"
          class="text-xl"
          :class="row.deactivated ? 'text-red-500' : 'text-green-500'"
      />
    </template>

    <template #protection-data="{ row } : { row: SchemaStudyApiRead }">
      <UIcon
          :name="row.no_permissions ? 'i-heroicons-lock-open-solid' : 'i-heroicons-lock-closed-solid'"
          :title="row.no_permissions ? 'Interviews können von allen angemeldeten Nutzenden durchgeführt werden' : 'Jeglicher Zugriff muss geregelt werden'"
          class="text-xl"
      />
    </template>

    <template #actions-data="{ row } : { row: SchemaStudyApiRead }">
      <UButton
          :to="`/manage/studies/${row.id}`"
          label="Bearbeiten"
          icon="i-heroicons-pencil"
          variant="outline"
          color="gray"
          class="mr-2"
          :disabled="!studyPermissionStore.currentUserCanManageStudy(row.id)"
      />
      <UButton
          :to="`/manage/studies/${row.id}/events`"
          label="Events verwalten"
          icon="i-heroicons-calendar-days"
          variant="outline"
          color="gray"
          class="mr-2"
          :disabled="!studyPermissionStore.currentUserCanManageStudy(row.id)"
      />
      <UButton
          :to="`/manage/studies/${row.id}/access`"
          :label="isStudyAccessManaged(row) ? 'Zugriff ansehen' : 'Zugriff bearbeiten'"
          icon="i-heroicons-key-solid"
          variant="outline"
          color="gray"
          class="mr-2"
          :disabled="!studyPermissionStore.currentUserCanManageUsers(row.id)"
      />
      <UButton
          :to="`/studies/${row.id}/export`"
          label="Datenexport"
          icon="i-heroicons-cloud-arrow-down"
          variant="outline"
          color="gray"
          :disabled="!studyPermissionStore.currentUserCanExport(row.id)"
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

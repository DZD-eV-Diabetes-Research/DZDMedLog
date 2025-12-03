<script setup lang="ts">
import type { SchemaStudyPermissionRead } from "#open-fetch-schemas/medlogapi";

const permissionLabels = ["Study Viewer", "Study Interviewer", "Study Admin"];
const columns = [{
  key: 'name',
  label: 'Name'
}, {
  key: 'email',
  label: 'Email'
}, {
  key: 'permissions',
  label: 'Zugriffsrechte'
}, {
  key: 'actions'
}];

const props = defineProps({
  permissions: { type: Array as () => SchemaStudyPermissionRead[], default: () => [] },
});

defineEmits(['delete-permissions', 'edit-permissions']);

const rows = computed(() => {
  return props.permissions.map(item => {
    return {
      id: item.id,
      studyId: item.study_id,
      userId: item.user_id,
      name: item.user_ref?.display_name ?? item.user_ref?.user_name ?? 'N/A',
      email: item.user_ref?.email ?? 'N/A',
      permissions: [item.is_study_viewer, item.is_study_interviewer, item.is_study_admin].map((value, index) => value ? permissionLabels[index] : null).filter(Boolean),
    };
  });
});
</script>

<template>
  <UTable :rows="rows" :columns="columns">
    <template #permissions-data="{ row }">
      <div v-if="row.permissions.length > 0" class="space-x-2">
        <UBadge
            v-for="permission in row.permissions" :key="permission"
            class="bg-white text-slate-500 border-2 border-slate-500 px-2 py-1 rounded-lg">
          {{ permission }}
        </UBadge>
      </div>
      <div v-else />
    </template>

    <template #actions-data="{ row }">
      <UButton
          label="Bearbeiten"
          icon="i-heroicons-pencil-square-20-solid"
          color="gray"
          variant="outline"
          class="mr-2"
          @click="$emit('edit-permissions', row.id)"
      />
      <UButton
          label="Widerrufen"
          icon="i-heroicons-user-minus"
          color="red"
          variant="outline"
          @click="$emit('delete-permissions', row.id)"
      />
    </template>
  </UTable>
</template>

<style scoped>

</style>

<script setup lang="ts">
import type { SchemaUser, SchemaUserRoleApiRead } from '#open-fetch-schemas/medlogapi'

const columns = [{
  key: 'name',
  label: 'Name',
  sortable: true,
}, {
  key: 'active',
  label: 'Aktiv'
}, {
  key: 'email',
  label: 'Email'
}, {
  key: 'roles',
  label: 'Globale Rollen'
}, {
  key: 'actions'
}]

const props = defineProps({
  loading: { type: Boolean, default: false },
  roles: { type: Array as () => SchemaUserRoleApiRead[], default: () => [] },
  users: { type: Array as () => SchemaUser[], default: () => [] },
});

defineEmits(['edit-roles']);

const sort = ref<{
  column: string;
  direction: "asc" | "desc";
}>({
  column: 'name',
  direction: 'asc'
})

const rows = computed(() => {
  return props.users.map(user => {
    // Inject a computed name property into each user, needed for sorting
    return Object.assign(user, { name: user.display_name ?? user.user_name })
  });
});
</script>

<template>
  <UTable :rows="rows" :columns="columns" :loading="loading" :sort="sort">
    <template #name-data="{ row }">
      {{ row.display_name ?? row.user_name }}
      <small v-if="row.display_name" class="block">{{ row.user_name }}</small>
    </template>
    <template #active-data="{ row }">
      <UIcon
          :name="row.deactivated ? 'i-heroicons-x-circle-solid' : 'i-heroicons-check-circle-solid'"
          class="text-xl"
          :class="row.deactivated ? 'text-red-500' : 'text-green-500'"
      />
    </template>

    <template #roles-data="{ row }">
      <div v-if="row.roles.length > 0" class="space-x-2" >
        <UBadge v-for="role in row.roles" :key="role" class="bg-white text-slate-500 border-2 border-slate-500 px-2 py-1 rounded-lg">
          {{ role }}
        </UBadge>
      </div>
      <div v-else>&mdash;</div>
    </template>

    <template #actions-data="{ row }">
      <UButton
          label="Rollen bearbeiten"
          icon="i-heroicons-key-solid"
          variant="outline"
          color="gray"
          @click="$emit('edit-roles', row.id)"
      />
    </template>
  </UTable>
</template>

<style scoped>

</style>

<script setup lang="ts">
const columns = [{
  key: 'user_name',
  label: 'Benutzername'
}, {
  key: 'email',
  label: 'Email'
}, {
  key: 'display_name',
  label: 'Angezeigter Name'
}, {
  key: 'roles',
  label: 'Rollen'
}, {
  key: 'actions'
}]

const props = defineProps({
  roles: { type: Array, default: () => [] },
  users: { type: Array, default: () => [] },
});

const emit = defineEmits(['patch-user']);

const expand = ref({
  openedRows: [],
  row: {}
})

const selectedRolesPerUser = ref<Record<string, string[]>>({})

// Here we alter the user array to a new form (mappedUsers) to visualize them in the template
const mappedUsers = computed(() => {
  if (!props.users) return [];
  return props.users.map(user => ({
    id: user.id,
    user_name: user.user_name,
    email: user.email,
    display_name: user.display_name,
    roles: user.roles,
    hasExpand: true
  }))
})

function isRowExpanded(row: any) {
  return expand.value.openedRows.some((r) => r.id === row.id)
}

function handleToggle(row: any) {
  const alreadyOpen = isRowExpanded(row)
  expand.value.openedRows = alreadyOpen ? [] : [row]
  selectedRolesPerUser.value[row.id] = [...row.roles]
}

function saveUser(row) {
  emit('patch-user', row.id, selectedRolesPerUser.value[row.id]);
}
</script>

<template>
  <UTable v-model:expand="expand" :rows="mappedUsers" :columns="columns">

    <template #roles-data="{ row }">
      <div v-if="row.roles.length > 0" class="space-x-2" >
        <UBadge v-for="role in row.roles" :key="role" class="bg-white text-slate-500 border-2 border-slate-500 px-2 py-1 rounded-lg">
          {{ role }}
        </UBadge>
      </div>
      <div v-else />
    </template>

    <template #expand="{ row }">
      <div class="flex flex-col p-4 bg-gray-50 rounded text-center items-center space-y-3">
        <p v-if="row.roles.length > 0">{{ row.user_name }} sind folgenden Rollen zugewiesen: </p>
        <p v-else>{{ row.user_name }} sind aktuell keinen Rollen zugewiesen</p>
        <div class="space-y-2 mb-20">
          <UCheckbox
              v-for="role in roles" :key="role.role_name"
              v-model="selectedRolesPerUser[row.id]" :value="role.role_name" :name="role.role_name"
              :label="role.role_name" />
        </div>
        <div class="mt-4">
          <UButton
              class="bg-white text-slate-500 border-2 border-slate-500 px-2 py-1 rounded-lg hover:bg-slate-500 hover:text-white"
              @click="saveUser(row)">
            Speichern</UButton>
        </div>
      </div>
    </template>

    <template #expand-action="{ row }">
      <UButton
          v-if="row.hasExpand"
          class="bg-white text-slate-500 border-2 border-slate-500 px-2 py-1 rounded-lg hover:bg-slate-500 hover:text-white"
          @click="handleToggle(row)">
        {{ isRowExpanded(row) ? 'Zuklappen' : 'Bearbeiten' }}
      </UButton>
    </template>
  </UTable>
</template>

<style scoped>

</style>

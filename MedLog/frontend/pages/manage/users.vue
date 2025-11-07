<script setup lang="ts">
import { useMedlogapi } from "#open-fetch";

const { data: users, refresh: refreshUsers } = useMedlogapi('/api/user')
const { data: roles } = useMedlogapi('/api/role')

const patchUser = async function (id: string, roles: string[]) {
  const { error } = await useMedlogapi(
      '/api/user/{id}',
      {
        method: "PATCH",
        body: {
          roles: roles
        },
        path: {
          id: id
        }
      }
  );

  if (error.value) {
    throw error.value;
  }

  await refreshUsers();
}
</script>

<template>
  <section class="container w-4/12 mx-auto">
    <h1 class="text-4xl font-normal text-center mb-4">Kontoverwaltung</h1>

    <UserManagementTable v-if="users" :roles="roles" :users="users.items ?? []" @patch-user="patchUser" />
    <p v-else>Lade Konten ...</p>

    <div class="text-center">
      <hr class="my-8 border-2">
      <h2 class="text-3xl font-semibold mb-4">Verfügbare Rollen</h2>
      <div v-for="role in roles" :key="role.role_name" class="flex flex-row justify-center mb-4">
        <p><span class="font-bold">{{ role.role_name }}</span>: {{ role.description }}</p>
      </div>
    </div>
  </section>
</template>

<style scoped>

</style>

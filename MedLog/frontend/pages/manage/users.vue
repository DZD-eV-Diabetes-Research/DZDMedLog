<script setup lang="ts">
const roleStore = useRoleStore();
const toast = useToast();
const userStore = useUserStore();

const roleModalOpen = ref(false);
const rolesForEditModal = ref([]);
const userIdForEditModal = ref('');
const usersPending = ref(false);

async function onEditUserRoles(userId: string) {
  try {
    const user = await useGetUser(userId);
    userIdForEditModal.value = userId;
    rolesForEditModal.value = user.roles;
    roleModalOpen.value = true;
  } catch (e) {
    toast.add({
      title: "Konnte User nicht laden",
      description: e.data?.detail ?? e.message ?? e,
    });
  }
}

async function onRoleModalSave(data) {
  try {
    const patchedUser = await usePatchUser(userIdForEditModal.value, { roles: data.roles });
    userStore.upsertUser(patchedUser);
    roleModalOpen.value = false;
  } catch (e) {
    toast.add({
      title: "Konnte Rollen nicht speichern",
      description: e.data?.detail ?? e.message ?? e,
    });
  }
}

onMounted(async () => {
  if (!userStore.isUserAdmin) {
    return;
  }

  usersPending.value = true;
  await userStore.loadUsers();
  usersPending.value = false;
});
</script>

<template>
  <section v-if="userStore.isUserAdmin" class="container w-11/12 lg:w-8/12 xl:w-6/12 mx-auto mt-8">
    <h1 class="text-4xl font-normal text-center mb-4">Kontoverwaltung</h1>

    <p class="my-4 text-center text-gray-500">
      Hier können systemweite Rechte mittels globaler Rollen vergeben oder entzogen werden.
    </p>

    <UserManagementTable
        :loading="usersPending"
        :roles="roleStore.availableRoles"
        :users="userStore.allUsers"
        @edit-roles="onEditUserRoles"
    />
    <UserManagementRoleModal
        v-model="roleModalOpen"
        :initial-roles="rolesForEditModal"
        prevent-close
        @cancel="roleModalOpen = false;"
        @save="onRoleModalSave"
    />
  </section>
  <section v-else class="container w-11/12 lg:w-8/12 xl:w-6/12 mx-auto mt-8">
    <ErrorMessage
        title="Keine Berechtigung"
        message="Ihnen fehlt die Berechtigung für diese Seite"
    />
  </section>
</template>

<style scoped>

</style>

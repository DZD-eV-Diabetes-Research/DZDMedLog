<script setup lang="ts">
import {
  ref,
  onMounted,
  useRoleStore,
  useToast,
  useUserStore,
  useGetUser,
} from "#imports";
import type {RoleFormSchema} from "~/components/UserManagement/RoleModal.vue";

const roleStore = useRoleStore();
const toast = useToast();
const userStore = useUserStore();

const activationModalVisible = ref(false);
const deactivationModalVisible = ref(false);
const roleModalOpen = ref(false);
const rolesForEditModal = ref<string[]>([]);
const userIdForEditModal = ref('');
const userIdToActivate = ref('');
const userIdToDeactivate = ref('');
const usersPending = ref(false);

async function activateUser(): Promise<void> {
  try {
    await userStore.setActive(userIdToActivate.value, true)
    activationModalVisible.value = false;
    userIdToActivate.value = ''
  } catch (error) {
    toast.add({
      title: "Konnte User nicht aktivieren",
      description: useGetErrorMessage(error),
    });
  }
}

async function deactivateUser(): Promise<void> {
  try {
    await userStore.setActive(userIdToDeactivate.value, false)
    deactivationModalVisible.value = false;
    userIdToDeactivate.value = ''
  } catch (error) {
    toast.add({
      title: "Konnte User nicht deaktivieren",
      description: useGetErrorMessage(error),
    });
  }
}

async function onActivateUser(userId: string) {
  userIdToActivate.value = userId;
  activationModalVisible.value = true;
}

async function onDeactivateUser(userId: string) {
  userIdToDeactivate.value = userId;
  deactivationModalVisible.value = true;
}

async function onEditUserRoles(userId: string) {
  try {
    const user = await useGetUser(userId);
    userIdForEditModal.value = userId;
    rolesForEditModal.value = user.roles ?? [];
    roleModalOpen.value = true;
  } catch (error) {
    toast.add({
      title: "Konnte User nicht laden",
      description: useGetErrorMessage(error),
    });
  }
}

async function onRoleModalSave(data: RoleFormSchema) {
  try {
    const patchedUser = await usePatchUser(userIdForEditModal.value, { roles: data.roles });
    userStore.upsertUser(patchedUser);
    roleModalOpen.value = false;
  } catch (error) {
    toast.add({
      title: "Konnte Rollen nicht speichern",
      description: useGetErrorMessage(error),
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
        @activate-user="onActivateUser"
        @deactivate-user="onDeactivateUser"
    />
    <UserManagementRoleModal
        v-model="roleModalOpen"
        :initial-roles="rolesForEditModal"
        prevent-close
        @cancel="roleModalOpen = false;"
        @save="onRoleModalSave"
    />
    <ConfirmationModal
        v-model="activationModalVisible"
        confirm-label="Aktivieren"
        @cancel="activationModalVisible = false"
        @confirm="activateUser"
    >
      <template #description>
        <p class="break-all">
          Möchten Sie den User
          <span class="font-semibold">{{ userStore.nameForUser(userIdToActivate) ?? 'N/A' }}</span>
          wirklich aktivieren?
        </p>
      </template>
    </ConfirmationModal>
    <ConfirmationModal
        v-model="deactivationModalVisible"
        :is-dangerous-to-confirm="true"
        confirm-label="Deaktivieren"
        @cancel="deactivationModalVisible = false"
        @confirm="deactivateUser"
    >
      <template #description>
        <p class="break-all">
          Möchten Sie den User
          <span class="font-semibold">{{ userStore.nameForUser(userIdToDeactivate) ?? 'N/A' }}</span>
          wirklich deaktivieren?
        </p>
      </template>
    </ConfirmationModal>
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

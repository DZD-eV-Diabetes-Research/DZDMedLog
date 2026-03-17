<script setup lang="ts">
import {
  computed,
  onMounted,
  ref,
  useDeletePermissions,
  useGetPermissions,
  useGetPermissionsByStudy,
  usePutPermissions,
  useRoute,
  useStudyStore,
  useToast,
  useUserStore
} from "#imports";
import type {
  SchemaStudyPermissionDesc,
  SchemaStudyPermissionRead,
  SchemaStudyPermissonUpdate
} from "#open-fetch-schemas/medlogapi";

const route = useRoute();
const studyStore = useStudyStore();
const toast = useToast();
const userStore = useUserStore();

const currentStudy = computed(() => studyStore.getStudy(studyId.value));
const studyId = computed(() => route.params.study_id as string);
const userIdsWithAccess = computed(() => {
  return studyPermissions.value.map((value) => value.user_id);
});
const usersWithoutAccessOptions = computed(() => {
  return userStore.allUsers
      .filter(user => {
        return !userIdsWithAccess.value.includes(user.id);
      })
      .map(user => {
        return {
          label: user.display_name ?? user.user_name ?? 'N/A',
          value: user.id,
        };
      });
});

const availablePermissions = ref<SchemaStudyPermissionDesc[]>([]);
const loading = ref(true);
const permissionsToEdit = ref<string[]>();
const studyPermissions = ref<SchemaStudyPermissionRead[]>([]);
const studyPermissionToDelete = ref();
const showEditModal = ref(false);
const showDeleteModal = ref(false);
const userIdToAddPermissionsFor = ref();
const userIdToEditPermissionsFor = ref();

async function loadStudyPermissions() {
  loading.value = true;
  studyPermissions.value = await useGetPermissionsByStudy(studyId.value);
  loading.value = false;
}

function onAddPermissions() {
  userIdToEditPermissionsFor.value = userIdToAddPermissionsFor.value;
  permissionsToEdit.value = [];
  showEditModal.value = true;
}

async function onDeletePermissions(studyPermissionId: string) {
  studyPermissionToDelete.value = studyPermissions.value.find((item) => item.id === studyPermissionId);
  showDeleteModal.value = true;
}

async function onDeletePermissionsConfirmation() {
  try {
    await useDeletePermissions(studyPermissionToDelete.value.study_id, studyPermissionToDelete.value.user_id);
    showDeleteModal.value = false;
  } catch (error) {
    toast.add({
      title: "Konnte Zugriff nicht widerrufen",
      description: useGetErrorMessage(error),
    });
  }
  await loadStudyPermissions();
}

function onEditPermissions(studyPermissionsId: string) {
  const studyPermission = studyPermissions.value.find((item) => item.id === studyPermissionsId);

  if (!studyPermission) {
    toast.add({
      title: "Konnte Berechtigungen nicht laden",
      description: `StudyPermissions-ID ${studyPermissionsId}`,
    });
    return;
  }

  userIdToEditPermissionsFor.value = studyPermission.user_ref?.id;
  const permissions: string[] = [];
  availablePermissions.value.forEach((item) => {
    if (Object.hasOwn(studyPermission, item.study_permission_name)) {
      const studyPermissionName = item.study_permission_name as keyof typeof studyPermission;
      if (studyPermission[studyPermissionName] === true) {
        permissions.push(studyPermissionName);
      }
    }
  })
  permissionsToEdit.value = permissions;
  showEditModal.value = true;
}

async function onSavePermissions(data: SchemaStudyPermissonUpdate) {
  try {
    await usePutPermissions(studyId.value, userIdToEditPermissionsFor.value, data);
    await loadStudyPermissions();
    userIdToAddPermissionsFor.value = undefined;
    showEditModal.value = false;
  } catch (error) {
    toast.add({
      title: "Fehler beim Speichern",
      description: useGetErrorMessage(error),
    });
  }
}

onMounted(async () => {
  availablePermissions.value = await useGetPermissions();
  await userStore.loadUsers();
  await loadStudyPermissions();
});
</script>

<template>
  <section v-if="userStore.isUserAdmin" class="container w-11/12 lg:w-8/12 xl:w-6/12 mx-auto mt-8">
    <div class="flex justify-center break-all mb-4 relative items-center">
      <div class="absolute left-0">
        <UButton
            to="/manage/studies"
            label="Zurück"
            title="Zur Studienverwaltung"
            variant="outline"
            color="gray"
            icon="i-heroicons-arrow-left-circle"
        />
      </div>
      <h1 class="text-4xl font-normal text-center w-8/12">
        Zugriffsrechte für {{ studyStore.nameForStudy(studyId) }}
      </h1>
    </div>

    <WarningMessage
        v-if="currentStudy?.no_permissions"
        title="Vereinfachtes Rechtemodell aktiv"
        message="Alle Nutzer haben das Recht, für diese Studie Interviews zu führen, auch wenn sie hier nicht aufgeführt sind."
        class="mb-4"
    />

    <StudyPermissionManagementTable
        :permissions="studyPermissions"
        :loading="loading"
        @edit-permissions="onEditPermissions"
        @delete-permissions="onDeletePermissions"
    />

    <hr class="m-8">

    <div class="flex flex-row items-center justify-center text-xl font-normal mb-4">
      <UIcon name="i-heroicons-user-plus-solid" class="mr-2" />
      <h2>Rechte vergeben</h2>
    </div>
    <div class="flex flex-col w-6/12 mx-auto">
      <UAlert
          v-if="usersWithoutAccessOptions.length === 0"
          description="Für alle Benutzer wurden bereits Rechte festgelegt."
          color="orange"
          variant="outline"
          class="mb-4"
      />
      <div class="flex flex-row gap-2 justify-center">
        <USelect
            v-model="userIdToAddPermissionsFor"
            :options="usersWithoutAccessOptions"
            placeholder="Benutzer auswählen"
        />
        <UButton label="Hinzufügen" :disabled="!userIdToAddPermissionsFor" @click="onAddPermissions" />
      </div>
    </div>

    <StudyPermissionManagementEditModal
        v-model="showEditModal"
        :available-permissions="availablePermissions"
        :initial-permissions="permissionsToEdit"
        @cancel="showEditModal = false"
        @save="onSavePermissions"
    />

    <ConfirmationModal
        v-model="showDeleteModal"
        :is-dangerous-to-confirm="true"
        confirm-label="Widerrufen"
        cancel-label="Abbrechen"
        @cancel="showDeleteModal = false"
        @confirm="onDeletePermissionsConfirmation"
    >
      <template #description>
        <p class="break-all">
          Möchten Sie den Zugriff auf
          <span class="font-semibold">{{ studyStore.nameForStudy(studyPermissionToDelete.study_id) }}</span>
          für
          <span class="font-semibold">{{ userStore.nameForUser(studyPermissionToDelete.user_id) }}</span>
          wirklich widerrufen?
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

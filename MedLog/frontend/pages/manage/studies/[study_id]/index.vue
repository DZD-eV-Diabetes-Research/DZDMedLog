<script setup lang="ts">
import type { SchemaStudyApiRead } from "#open-fetch-schemas/medlogapi";
import type { StudyFormSchema } from "~/components/StudyManagement/Form.vue";
import { isNormalizationChangeError } from "~/type-helper";
import { ConfirmationModal } from "#components";

const configStore = useConfigStore();
const modal = useModal();
const route = useRoute();
const studyPermissionStore = useStudyPermissionStore();
const studyStore = useStudyStore();
const toast = useToast();
const userStore = useUserStore();

const studyId = route.params.study_id as string;

const nameChangeAccepted = ref<boolean>(false);
const studyToEdit = ref<SchemaStudyApiRead>();

const isStudyAccessManaged = computed(() => {
  return configStore.branding.disableUiPermissionManagement === true || studyToEdit.value?.is_oidc_permission_managed === true
})

async function onCancel() {
  await navigateTo('/manage/studies');
}

async function onSubmit(data: StudyFormSchema, forceUpdate: boolean = false): Promise<void> {
  if (isStudyAccessManaged.value && nameChangeAccepted.value !== true && data.display_name !== studyStore.studyById(studyId)?.display_name) {
    modal.open(ConfirmationModal, {
      onCancel: modal.close,
      onConfirm: async () => {
        await modal.close();
        nameChangeAccepted.value = true;
        await onSubmit(data);
      },
      description: 'Wenn der Name der Studie geändert wird, muss dieser auch im STUDY_PERMISSION_MAPPING angepasst werden.',
      isDangerousToConfirm: true,
    })
    return;
  }

  try {
    const updatedStudy = await usePatchStudy(studyId, data, forceUpdate);
    studyStore.upsertStudy(updatedStudy);
    await navigateTo('/manage/studies')
  } catch (error) {
    if (isNormalizationChangeError(error)) {
      modal.open(ConfirmationModal, {
        onCancel: modal.close,
        onConfirm: async () => {
          await modal.close();
          await onSubmit(data, true);
        },
          description: `Das Ändern der Normalisierung kann dazu führen, dass Probanden bei Suchvorgängen stillschweigend zusammengeführt oder aufgeteilt werden. Rückwirkend findet keine Anpassung der Probanden-IDs statt. Es wurden bereits ${error.data.detail.affected_interview_count} Interviews für diese Studie geführt.`,
        isDangerousToConfirm: true,
      })
      return;
    }
    toast.add({
      title: "Fehler beim Speichern",
      description: useGetErrorMessage(error),
    });
  }
}

onBeforeMount(async () => {
  studyToEdit.value = studyStore.getStudy(studyId);
});
</script>

<template>
  <section v-if="userStore.isAdmin || studyPermissionStore.currentUserCanManageStudy(studyId)" class="container w-11/12 lg:w-8/12 xl:w-6/12 mx-auto mt-8">
    <h1 class="text-4xl font-normal text-center mb-4">Studie bearbeiten</h1>

    <StudyManagementForm
        :initial-state="studyToEdit"
        :is-no-permission-blocked="isStudyAccessManaged && !userStore.isAdmin"
        @cancel="onCancel"
        @save="onSubmit"
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

<script setup lang="ts">
import { type InferType, object, string } from "yup";
import type {FormSubmitEvent} from "#ui/types";
import type {SchemaStudyApiRead} from "#open-fetch-schemas/medlogapi";

const studyPermissionStore = useStudyPermissionStore();

const props = defineProps({
  study: { type: Object as () => SchemaStudyApiRead, required: true },
})

const probandIdValidationError = ref('')

const state = reactive({
  probandId: '',
});

const schema = object({
  probandId: string().max(256).required('Die Probanden-ID wird benötigt'),
})

type Schema = InferType<typeof schema>

const isAllowedToCallUpProband = computed(() => {
  return studyPermissionStore.currentUserCanInterview(props.study.id) || studyPermissionStore.currentUserCanExport(props.study.id);
});

async function onSubmit(event: FormSubmitEvent<Schema>) {
  const { data, error } = await useMedlogapi('/api/study/{study_id}/proband-external-id/validate', {
    method: 'POST',
    path: {
      study_id: props.study.id
    },
    body: {
      proband_external_id: event.data.probandId
    }
  })

  if (error.value) {
    probandIdValidationError.value = useGetErrorMessage(error.value)
    return
  }

  if (data.value?.valid === true) {
    navigateTo(`/studies/${props.study.id}/proband/${data.value.normalized_proband_external_id}`)
  } else {
    probandIdValidationError.value = data.value?.error_text ?? 'Die eingegebene Probanden-ID hat ein ungültiges Format.'
  }
}
</script>

<template>
  <UCard>
    <template #header>
      <div class="flex flex-row justify-between">
        <div class="inline-flex text-lg break-words">
          {{ study.display_name }}
          <UBadge v-if="study.deactivated" icon="i-heroicons-archive-box" label="Deaktiviert" color="gray" size="md" class="ml-2"/>
        </div>
        <UButton
            v-if="studyPermissionStore.currentUserCanExport(study.id)"
            :to="`/studies/${study.id}/export`"
            label="Datenexport"
            icon="i-heroicons-cloud-arrow-down"
            variant="outline"
            color="gray"
        />
      </div>
    </template>

    <UForm :schema="schema" :state="state" :validate-on="['submit']" @submit="onSubmit">
      <div class="flex flex-row gap-2">
        <UFormGroup
            label="Probanden-ID"
            name="probandId"
            :help="study.proband_external_id_example ? `Beispiel: ${study.proband_external_id_example}` : ''"
            :error="probandIdValidationError"
        >
          <UInput v-model.trim="state.probandId" autocomplete="off" />
        </UFormGroup>
        <div class="content-top mt-6">
          <UTooltip text="Sie sind nicht berechtigt, Interviews zu führen" :popper="{ arrow: true }" :prevent="isAllowedToCallUpProband">
            <UButton type="submit" color="primary" :disabled="!isAllowedToCallUpProband">
              Proband aufrufen
            </UButton>
          </UTooltip>
        </div>
      </div>
    </UForm>
  </UCard>
</template>

<style scoped>

</style>

<script setup lang="ts">
import type { Study } from '~/stores/studyStore'
import { type InferType, object, string } from "yup";
import type {FormSubmitEvent} from "#ui/types";

const props = defineProps({
  study: { type: Object as () => Study, required: true },
})

const state = reactive({
  probandId: '',
});

const schema = object({
  probandId: string().required('Die Probanden-ID wird benötigt'),
})

type Schema = InferType<typeof schema>

function onSubmit(event: FormSubmitEvent<Schema>) {
  navigateTo(`/studies/${props.study.id}/proband/${event.data.probandId}`)
}
</script>

<template>
  <UCard>
    <template #header>
      <div class="text-lg break-words">
        {{ study.display_name }}
      </div>
    </template>

    <UForm :schema="schema" :state="state" :validate-on="['submit']" @submit="onSubmit">
      <div class="flex flex-row gap-2">
        <UFormGroup label="Probanden-ID" name="probandId">
          <UInput v-model.trim="state.probandId" autocomplete="off" />
        </UFormGroup>
        <div class="content-end">
          <UButton type="submit" color="primary">
            Proband aufrufen
          </UButton>
        </div>
      </div>
    </UForm>
  </UCard>
</template>

<style scoped>

</style>

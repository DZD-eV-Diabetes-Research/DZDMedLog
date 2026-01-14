<script setup lang="ts">
import { reactive, watch } from "#imports";
import { object, string } from "yup";

const modelValue = defineModel<boolean>();

const emit = defineEmits<{
  createStudy: [name: string];
}>();

const state = reactive({
  studyName: "",
});

const schema = object({
  studyName: string().max(128, "Der Name kann maximal 128 Zeichen lang sein").required("Bitte geben Sie den Namen der Studie an"),
});

function onClose() {
  modelValue.value = false;
}

function createStudy() {
  emit("createStudy", state.studyName.trim());
}

watch(modelValue, (isOpen) => {
  // Reset form state on visibility change
  if (isOpen) {
    state.studyName = "";
  }
})
</script>

<template>
  <UModal v-model="modelValue" prevent-close>
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-lg">Studie anlegen</span>
          <UButton color="gray" variant="ghost" icon="i-heroicons-x-mark-20-solid" class="-my-1" @click="onClose" />
        </div>
      </template>

      <slot name="error" />

      <UForm :schema="schema" :state="state" class="space-y-4 mt-2" @submit="createStudy">
        <UFormGroup label="Name der Studie" name="studyName">
          <UInput v-model="state.studyName" required />
        </UFormGroup>
        <div class="flex justify-between">
          <UButton label="Abbrechen" color="gray" variant="outline" @click.prevent="onClose" />
          <UButton type="submit" label="Studie anlegen" />
        </div>
      </UForm>
    </UCard>
  </UModal>
</template>

<style scoped>

</style>

<script setup lang="ts">
import { reactive, watch } from "#imports";
import type { SchemaStudyPermissionDesc } from "#open-fetch-schemas/medlogapi";
import type { FormSubmitEvent } from "#ui/types";

const props = defineProps({
  availablePermissions: { type: Array as () => SchemaStudyPermissionDesc[], default: () => [] },
  initialPermissions: { type: Array as () => string[], default: () => [] },
});

const modelValue = defineModel<boolean>();

const emit = defineEmits(['cancel', 'save'])

type PermissionFormSchema = {
  permissions: string[];
};

const state = reactive<PermissionFormSchema>({
  permissions: [],
})

function onSubmit(event: FormSubmitEvent<PermissionFormSchema>) {
  const permissions = {} as Record<string, boolean>;
  props.availablePermissions.forEach((item) => {
    permissions[item.study_permission_name] = event.data.permissions.includes(item.study_permission_name);
  })
  emit('save', permissions);
}

watch(() => props.initialPermissions, (newValue) => {
  state.permissions = [];
  for (const availablePermission of props.availablePermissions) {
    if (newValue.includes(availablePermission.study_permission_name)) {
      state.permissions.push(availablePermission.study_permission_name);
    }
  }
});
</script>

<template>
  <DZDUIModal v-model="modelValue" title="Zugriff bearbeiten" @cancel="$emit('cancel')">
    <UForm :state="state" class="space-y-4" @submit="onSubmit">
      <UCheckbox
          v-for="permission in availablePermissions"
          :key="permission.study_permission_name"
          v-model="state.permissions"
          :label="permission.study_permission_name"
          :help="permission.description ?? ''"
          :value="permission.study_permission_name"
          class="mb-2"
      />
      <hr>
      <div class="flex justify-between">
        <UButton label="Abbrechen" variant="outline" @click.prevent="$emit('cancel')" />
        <UButton type="submit" label="Speichern" />
      </div>
    </UForm>
  </DZDUIModal>
</template>

<style scoped>

</style>

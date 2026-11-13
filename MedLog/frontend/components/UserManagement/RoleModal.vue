<script setup lang="ts">
import { reactive, useRoleStore, watch } from "#imports";
import type {FormSubmitEvent} from "#ui/types";

const roleStore = useRoleStore();
const props = defineProps({
  initialRoles: { type: Array, default: () => [] },
});

const modelValue = defineModel<boolean>();

const emit = defineEmits<{
  cancel: [],
  save: [data: RoleFormSchema],
}>()

export type RoleFormSchema = {
  roles: string[];
};

const state = reactive<RoleFormSchema>({
  roles: [],
})

function onSubmit(event: FormSubmitEvent<RoleFormSchema>) {
  emit('save', event.data);
}

watch(() => props.initialRoles, (newRoles) => {
  state.roles = [];
  for (const role of roleStore.availableRoles) {
    if (newRoles.includes(role.role_name)) {
      state.roles.push(role.role_name);
    }
  }
});
</script>

<template>
  <DZDUIModal v-model="modelValue" title="Rollen bearbeiten" @cancel="$emit('cancel')">
    <UForm :state="state" class="space-y-4" @submit="onSubmit">
      <UCheckbox
          v-for="role in roleStore.availableRoles"
          :key="role.role_name"
          v-model="state.roles"
          :label="role.role_name"
          :help="role.description ?? ''"
          :value="role.role_name"
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

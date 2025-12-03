<script setup lang="ts">
import { watch } from "vue";

const props = defineProps({
  availablePermissions: { type: Array, default: () => [] },
  initialPermissions: { type: Array, default: () => [] },
});

const emit = defineEmits(['cancel', 'save'])

const state = reactive({
  permissions: [],
})

function onSubmit(event) {
  const permissions = {};
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
  <UModal prevent-close>
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-lg">Zugriff bearbeiten</span>
          <UButton color="gray" variant="ghost" icon="i-heroicons-x-mark-20-solid" class="-my-1" @click="$emit('cancel')" />
        </div>
      </template>

      <UForm :state="state" class="space-y-4" @submit="onSubmit">
        <UCheckbox
            v-for="permission in availablePermissions"
            :key="permission.study_permission_name"
            v-model="state.permissions"
            :label="permission.study_permission_name"
            :help="permission.description"
            :value="permission.study_permission_name"
            class="mb-2"
        />
        <hr>
        <div class="flex justify-between">
          <UButton label="Abbrechen" variant="outline" @click.prevent="$emit('cancel')" />
          <UButton type="submit" label="Speichern" />
        </div>
      </UForm>
    </UCard>
  </UModal>
</template>

<style scoped>

</style>

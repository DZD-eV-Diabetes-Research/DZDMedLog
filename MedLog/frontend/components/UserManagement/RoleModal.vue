<script setup lang="ts">
import { watch } from "vue";

const roleStore = useRoleStore();
const props = defineProps({
  initialRoles: { type: Array, default: () => [] },
});

const emit = defineEmits(['cancel', 'save'])

const state = reactive({
  roles: [],
})

function onSubmit(event) {
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
  <UModal>
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-lg">Rollen bearbeiten</span>
          <UButton color="gray" variant="ghost" icon="i-heroicons-x-mark-20-solid" class="-my-1" @click="$emit('cancel')" />
        </div>
      </template>

      <UForm :state="state" class="space-y-4" @submit="onSubmit">
        <UCheckbox
            v-for="role in roleStore.availableRoles"
            :key="role.role_name"
            v-model="state.roles"
            :label="role.role_name"
            :help="role.description"
            :value="role.role_name"
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

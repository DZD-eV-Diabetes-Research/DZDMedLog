<script setup lang="ts">
import { object, string } from "yup";

defineEmits(['login'])

const schema = object({
  username: string().required("Benötigt"),
  password: string().required("Benötigt"),
});

const state = reactive({
  username: "",
  password: "",
});
</script>

<template>
  <UForm :schema="schema" :state="state" class="space-y-4" @submit="$emit('login', {username: state.username, password: state.password})">
    <UFormGroup name="username">
      <div class="flex justify-start my-2">
        <h3 class="text-lg font-medium">Benutzername</h3>
      </div>
      <UInput v-model="state.username" />
    </UFormGroup>
    <UFormGroup name="password">
      <div class="flex justify-start my-2">
        <h3 class="text-lg font-medium">Password</h3>
      </div>
      <UInput v-model="state.password" type="password" />
    </UFormGroup>
    <div class="flex justify-center">
      <UButton
          color="green" variant="soft"
          class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white"
          type="submit">
        Einloggen
      </UButton>
    </div>
  </UForm>
</template>

<style scoped>

</style>

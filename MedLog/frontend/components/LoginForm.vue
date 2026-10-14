<script setup lang="ts">
import { type InferType, object, string } from "yup";
import type { FormSubmitEvent } from "#ui/types";

interface Props {
  loading?: boolean;
  locked?: boolean;
}

withDefaults(defineProps<Props>(), {
  loading: false,
  locked: false,
})

const emits = defineEmits<{
  login: [username: string, password: string];
}>();

const schema = object({
  username: string().required("Pflichtfeld"),
  password: string().required("Pflichtfeld"),
});

const state = reactive({
  username: "",
  password: "",
});

type LoginFormSchema = InferType<typeof schema>;

function submitForm(event: FormSubmitEvent<LoginFormSchema>) {
  emits('login', event.data.username, event.data.password)
}
</script>

<template>
  <UForm :schema="schema" :state="state" class="space-y-4" :validate-on="['submit']" @submit.prevent="submitForm">
    <UFormGroup label="Benutzername" name="username">
      <UInput v-model="state.username" :disabled="locked" />
    </UFormGroup>
    <UFormGroup label="Passwort" name="password">
      <UInput v-model="state.password" type="password" :disabled="locked" />
    </UFormGroup>
    <div class="flex justify-center">
      <UButton type="submit" :disabled="locked" :loading="loading" block>
        Einloggen
      </UButton>
    </div>
  </UForm>
</template>

<style scoped>

</style>

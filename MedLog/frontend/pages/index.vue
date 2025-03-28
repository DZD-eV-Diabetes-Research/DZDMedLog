<template>
  <Layout>
    <UIBaseCard>
      <UForm :schema="schema" :state="state" class="space-y-4"
        @submit="tokenStore.login(state.username, state.password)">
        <div style="text-align: center">
          <h3 v-if="tokenStore.my_401" style="color:red">Wrong username or password</h3>
        </div>
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
          <UButton color="green" variant="soft"
            class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" type="submit">
            Einloggen
          </UButton>
        </div>
      </UForm>
      <div class="loginButtonContainer">
        <UButton @click="loginWithAuth()" color="red" variant="soft" label="Login mit DZD Authentik"
          class="border border-red-500 hover:bg-white hover:border-red-500 hover:text-red-500">
          <template #trailing>
            <img src="/public/icons/authentik-orange.svg" alt="DZD Authentik" style="width: 24px; height: 24px;" />
          </template>
        </UButton>
      </div>
      <p>
        Kein Account?
        <a href="https://auth.dzd-ev.org/" target="_blank">Registrieren Sie sich hier.</a>
      </p>
    </UIBaseCard>
  </Layout>
</template>

<script setup lang="ts">
const runtimeConfig = useRuntimeConfig()
const tokenStore = useTokenStore();
tokenStore.my_401 = false

import { object, string, type InferType } from "yup";
import type { FormSubmitEvent } from "#ui/types";

const schema = object({
  username: string().required("Benötigt"),
  password: string().required("Benötigt"),
});

type Schema = InferType<typeof schema>;

const state = reactive({
  username: undefined,
  password: undefined,
});

async function loginWithAuth() {
  try {
    await $fetch(`${runtimeConfig.public.baseURL}/auth/oidc/login/openid-connect`, {
      method: "GET",
      redirect: "follow"})
    window.location.href = `${runtimeConfig.public.baseURL}/auth/oidc/login/openid-connect`
    console.log(`${runtimeConfig.public.baseURL}/auth/oidc/login/openid-connect`);

  } catch (error) {
    console.log(error);

  }
}

</script>

<style scoped>
.loginButtonContainer {
  margin: 2%;
}
</style>
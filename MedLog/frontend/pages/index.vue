<template>
  <Layout>
    <UIBaseCard>
      <div>
        <UForm
          :schema="schema"
          :state="state"
          class="space-y-4"
          @submit="tokenStore.login(state.username, state.password)"
        >
        <div style="text-align: center">
          <h3 v-if="tokenStore.my_401" style="color:red">Wrong username or password</h3>
        </div>  
          <UFormGroup label="User Name" name="username">
            <UInput v-model="state.username" />
          </UFormGroup>
          <UFormGroup label="Password" name="password">
            <UInput v-model="state.password" type="password" />
          </UFormGroup>
          <div class="flex justify-center">
            <UButton
              color="green"
              variant="soft"
              class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white"
              type="submit"
            >
              Submit
            </UButton>
          </div>
        </UForm>
        <UButton @click="loginWithAuth()"
        color="blue"
              variant="soft"
              class="border border-blue-500 hover:bg-blue-300 hover:border-white hover:text-white">Login with DZD Authentic</UButton>
        <p>
          No account?
          <a href="https://auth.dzd-ev.org/" target="_blank">Sign Up</a>
        </p>
      </div>
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
  username: string().required("Required"),
  password: string().required("Required"),
});

type Schema = InferType<typeof schema>;

const state = reactive({
  username: undefined,
  password: undefined,
});

async function loginWithAuth() {
  try {
    await $fetch(`${runtimeConfig.public.baseURL}/auth/oidc/login/openid-connect`, {
      method: "GET",})
    console.log(`${runtimeConfig.public.baseURL}/auth/oidc/login/openid-connect`);
    
  } catch (error) {
    console.log(error);
    
  }
}

</script>
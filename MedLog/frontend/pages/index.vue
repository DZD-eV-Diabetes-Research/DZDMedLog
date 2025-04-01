<template>
  <Layout>
    <UIBaseCard>
      <div v-if="healthStatus?.healthy">
        <UForm :schema="schema" :state="state" class="space-y-4" @submit="login()">
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
        <div class="loginButtonContainer" v-if="data">
          <div v-for="loginMethod in data">
            <UButton v-if="loginMethod.name !== 'Login'" :class="[getRandomColorClass(), 'rounded-lg']"
              @click="loginOIDC(loginMethod)">
              Login via: {{ loginMethod.name }}
            </UButton>
          </div>
        </div>
        <p>
          Kein Account?
          <a href="https://auth.dzd-ev.org/" target="_blank">Registrieren Sie sich hier.</a>
        </p>
      </div>
      <div v-else class="flex flex-col space-y-8 text-center">
        <h3 class="text-4xl text-red-500">Backened status is not healthy</h3>
        <p class="text-lg text-red-500">Please start the backend or notify the admin</p>
        <p class="text-lg text-red-500">{{ healthError }}
        </p>
      </div>
    </UIBaseCard>
  </Layout>
</template>

<script setup lang="ts">

const runtimeConfig = useRuntimeConfig()
const tokenStore = useTokenStore();
tokenStore.set401(false);

import { object, string, type InferType } from "yup";

const { data: healthStatus, error:healthError } = await useFetch(`${runtimeConfig.public.baseURL}health`, {
  method: "GET",
})

const schema = object({
  username: string().required("Benötigt"),
  password: string().required("Benötigt"),
});

type Schema = InferType<typeof schema>;

const state = reactive({
  username: "",
  password: "",
});

const { data } = await useFetch(`${runtimeConfig.public.baseURL}auth/schemes`, {
  method: "GET",
  headers: { 'Authorization': "Bearer " + tokenStore.access_token },
})

const login = () => {
  try {
    tokenStore.login(state.username, state.password)
  } catch (error) {
    console.error(error);
  }
}

const loginOIDC = async function (oidc_method) {
  try {
    window.location.href = `${runtimeConfig.public.baseURL.slice(0, -1)}${oidc_method.login_endpoint}`
  } catch (error) {
    console.log(error);

  }
}

const colors = ["border border-fuchsia-400 bg-fuchsia-100 hover:bg-fuchsia-300 hover:border-white text-fuchsia-400 hover:text-white", "border bg-purple-100 border-purple-400 hover:bg-purple-300 hover:border-white text-purple-400 hover:text-white", "border bg-indigo-100 border-indigo-400 hover:bg-indigo-300 hover:border-white text-indigo-400 hover:text-white", "border bg-violet-100 border-violet-400 hover:bg-violet-300 hover:border-white text-violet-400 hover:text-white",
];
function getRandomColorClass() {
  const color = colors[Math.floor(Math.random() * colors.length)];
  return color;
}
</script>

<style scoped>
.loginButtonContainer {
  margin: 2%;
}
</style>
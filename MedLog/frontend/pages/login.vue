<template>
  <div>
    <UIBaseCard>
      <div v-if="healthCheckStore.healthy" class="flex flex-col justify-center">
        <div v-if="authStore.allSchemes" class="flex flex-col space-y-2">
          <ErrorMessage v-if="loginError" :error="loginError" />
          <div v-for="authScheme in authStore.allSchemes" :key="authScheme.auth_type">
            <LoginForm
              v-if="authScheme.auth_type === 'basic'"
              @login="({username, password}) => login(authScheme, username, password)"
            />
            <div v-else>
              <UButton class="rounded-lg" @click="authStore.doOIDCLogin(authScheme)">
                Login via: {{ authScheme.display_name }}
              </UButton>
            </div>
          </div>
        </div>
        <div class="mt-4">
          <p>
            Kein Account?
            <a
              href="https://auth.dzd-ev.org/" target="_blank"
              class="hover:border-[#ec372d] hover:border-b-2">Registrieren Sie sich hier.</a>
          </p>
        </div>
      </div>
      <div v-else class="flex flex-col space-y-8 text-center">
        <h3 class="text-4xl text-red-500">Der Backendstatus ist "not healthy"</h3>
        <p class="text-lg text-red-500">Bitte wenden Sie sich an ihren Admin</p>
      </div>
    </UIBaseCard>
  </div>
</template>

<script setup lang="ts">
import type { SchemaAuthSchemeInfo } from "#open-fetch-schemas/medlogapi";

const authStore = useAuthStore();
const healthCheckStore = useHealthCheckStore();
const userStore = useUserStore();

const loginError = ref();

async function login(authScheme: SchemaAuthSchemeInfo, username: string, password: string) {
  loginError.value = undefined;
  try {
    await authStore.doBasicLogin(authScheme, username, password);
    await userStore.setUserInfo()
    await navigateTo('/')
  } catch (error) {
    loginError.value = error;
  }
}

onMounted(async () => {
  await authStore.fetchAllAuthSchemes()

  if (healthCheckStore.healthy && authStore.autoLoginAvailable) {
    try {
      await authStore.doAutoLogin();
    } catch (error) {
      loginError.value = error;
    }
  }
})
</script>

<template>
  <section class="container w-11/12 lg:w-8/12 xl:w-6/12 mx-auto mt-8">
    <WarningMessage
        v-if="healthCheckStore.healthy === false"
        message="Das System ist derzeit nicht voll funktionsfähig"
        class="mb-4"
    />

    <ErrorMessage v-if="authStore.loginError" :error="authStore.loginError" class="mb-4" />

    <div class="flex flex-col items-center justify-center">
      <UCard class="w-96">
        <template #header>
          Willkommen bei DZDMedLog
        </template>

        <div class="flex flex-col gap-4">
          <div v-if="authStore.isLocalLoginAvailable">
            <LoginForm
              :loading="authStore.loginInProgress && authStore.loginInProgressProviderSlug === null"
              :locked="authStore.loginInProgress"
              @login="(username, password) => login(authStore.localLoginScheme!, username, password)"
            />
          </div>

          <UDivider
              v-if="authStore.isLocalLoginAvailable && authStore.oidcLoginSchemes?.length"
              label="oder Login via"
              orientation="horizontal"
              class="mb-4"
          />

          <div v-if="authStore.oidcLoginSchemes?.length" class="flex flex-col gap-4">
            <UButton
                v-for="authScheme in authStore.oidcLoginSchemes"
                :key="authScheme.provider_slug!"
                color="gray"
                variant="solid"
                trailing-icon="i-heroicons-arrow-right-circle"
                class="justify-center"
                :disabled="authStore.loginInProgress"
                :loading="authStore.loginInProgress && authStore.loginInProgressProviderSlug === authScheme.provider_slug"
                @click.once="authStore.doOIDCLogin(authScheme)"
            >
              {{ authScheme.display_name }}
            </UButton>
          </div>
        </div>
      </UCard>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { SchemaAuthSchemeInfo } from "#open-fetch-schemas/medlogapi";

const authStore = useAuthStore();
const healthCheckStore = useHealthCheckStore();
const userStore = useUserStore();

async function login(authScheme: SchemaAuthSchemeInfo, username: string, password: string) {
  await authStore.doBasicLogin(authScheme, username, password);
  if (!authStore.loginError) {
    await userStore.setUserInfo()
    await navigateTo('/')
  }
}

onMounted(async () => {
  await authStore.fetchAllAuthSchemes()

  if (healthCheckStore.healthy && authStore.autoLoginAvailable) {
    await authStore.doAutoLogin();
  }
})
</script>

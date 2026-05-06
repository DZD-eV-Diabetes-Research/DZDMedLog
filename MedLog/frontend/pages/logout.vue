<script setup lang="ts">
const { $medlogapi } = useNuxtApp()
const drugDbUpdaterStore = useDrugDbUpdaterStore();
const drugFieldStore = useDrugFields();
const eventStore = useEventStore();
const healthCheckStore = useHealthCheckStore();
const interviewStore = useInterviewStore();
const roleStore = useRoleStore();
const studyStore = useStudyStore();
const systemAnnouncementsStore = useSystemAnnouncementsStore();
const userStore = useUserStore();

const logoutError = ref();

onMounted(async () => {
  let endSessionUrl: string | null = null;

  try {
    const response = await $medlogapi("/api/auth/logout", {
      method: 'POST'
    }) as { end_session_url?: string } | null;
    endSessionUrl = response?.end_session_url ?? null;
  } catch (error) {
    // Ignore a 401 error here, because being not authorized is our goal.
    if (!(error instanceof Error && 'statusCode' in error && error.statusCode === 401)) {
      logoutError.value = error;
      return;
    }
  }

  // Clear the stores, either because of successful logout or an ignored 401 error
  interviewStore.$reset();
  eventStore.$reset();
  studyStore.$reset();
  drugFieldStore.$reset();
  userStore.$reset();
  roleStore.$reset();
  drugDbUpdaterStore.$reset();

  // Public and internal announcements are mixed, let's remove them all and fetch the public ones again
  systemAnnouncementsStore.$reset();
  await systemAnnouncementsStore.fetchSystemAnnouncements();

  // Wipe the full report and fetch the public basic info again
  healthCheckStore.$reset();
  await healthCheckStore.doSimpleHealthCheck();

  // For OIDC logout: navigate the browser to the IdP's end_session_endpoint so the
  // IdP session is terminated. The IdP will redirect back to the app root afterwards.
  if (endSessionUrl) {
    window.location.href = endSessionUrl;
    return;
  }
})
</script>

<template>
  <div class="mt-8 w-11/12 lg:w-8/12 xl:w-6/12 mx-auto">
    <h1 class="text-4xl font-normal text-center mb-8">Logout</h1>

    <ErrorMessage v-if="logoutError" :error="logoutError" />
    <div v-else-if="!userStore.isLoggedIn" class="text-center text-lg">
      <p class="mb-4">Sie sind abgemeldet.</p>
      <UButton
          to="/login"
          variant="outline"
          icon="i-heroicons-arrow-right-end-on-rectangle"
      >
        Wieder anmelden
      </UButton>
    </div>
    <div v-else class="text-center text-lg">
      Sie werden abgemeldet ...
      <UProgress animation="carousel" class="mt-4" />
    </div>
  </div>
</template>

<style scoped>

</style>

<template>
  <LayoutHeader />
  <NuxtPage />
  <LayoutFooter />
  <UNotifications />
</template>

<script setup lang="ts">
const configStore = useConfigStore();
const drugFieldsStore = useDrugFields();
const healthCheckStore = useHealthCheckStore();
const studyStore = useStudyStore();
const userStore = useUserStore();

useHead(() => ({
  title: configStore.appName,
  meta: [
    { name: 'description', content: 'DZD Webapp to audit medication for clinical studies' }
  ],
  htmlAttrs: {
    lang: 'de',
  },
}))

// Check health of the backend
try {
  await healthCheckStore.doSimpleHealthCheck();
} catch (error) {
  throw createError({
    message: 'Die Anwendung ist derzeit nicht funktionsfähig',
    cause: error,
    fatal: true,
  });
}

if (userStore.isLoggedIn) {
  await healthCheckStore.doFullHealthCheck();

  // Set up basic global data
  try {
    await configStore.fetchAllConfigs();
    await studyStore.loadAvailableStudies();
    await drugFieldsStore.fetchFields();
    await drugFieldsStore.fetchCodes();
  } catch (error) {
    throw createError({
      message: 'Konnte elementare Daten nicht abrufen',
      cause: error,
      fatal: true,
    })
  }
} else {
  await navigateTo('/login');
}

</script>

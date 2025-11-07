<template>
  <LayoutHeader />
  <NuxtPage />
  <LayoutFooter />
</template>

<script setup lang="ts">
useHead({
  title: 'DZD Medlog',
  meta: [
    { name: 'description', content: 'DZD Webapp to audit medication for clinical studies' }
  ],
})

const drugFieldsStore = useDrugFields();
const healthCheckStore = useHealthCheck();
const studyStore = useStudyStore();
const userStore = useUserStore();

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
    await studyStore.getAvailableStudies();
    await drugFieldsStore.fetchFields();
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

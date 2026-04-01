<template>
  <LayoutHeader />
  <NuxtPage id="content-wrap" />
  <LayoutFooter />
  <UNotifications />
</template>

<script setup lang="ts">
const configStore = useConfigStore();
const drugDbUpdaterStore = useDrugDbUpdaterStore();
const drugFieldsStore = useDrugFields();
const healthCheckStore = useHealthCheckStore();
const roleStore = useRoleStore();
const studyStore = useStudyStore();
const systemAnnouncementsStore = useSystemAnnouncementsStore();
const toast = useToast();
const userStore = useUserStore();

const statusRefreshIntervalDelay = 60000;

const statusRefreshInterval = ref<NodeJS.Timeout | null>(null);

useHead(() => ({
  title: configStore.appName,
  meta: [
    { name: 'description', content: 'DZD Webapp to audit medication for clinical studies' }
  ],
  htmlAttrs: {
    lang: 'de',
  },
}))

async function refreshStatus() {
  try {
    await healthCheckStore.doSimpleHealthCheck();
    await healthCheckStore.doFullHealthCheck();
    await systemAnnouncementsStore.fetchSystemAnnouncements();
    await drugDbUpdaterStore.fetchStatus();
  } catch (error) {
    toast.add({
      title: 'Konnte Systemstatus nicht abfragen',
      description: isNuxtError(error) ? error.statusMessage : String(error),
      actions: [{ click: refreshStatus, label: 'Jetzt erneut versuchen' }],
      timeout: statusRefreshIntervalDelay,
    })
  }
}

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

try {
  await roleStore.loadRoles()
  await userStore.setUserInfo()
} catch (error) {
  // Swallow 401 errors, they are handled separately
  if (!(isNuxtError(error) && error.statusCode == 401)) {
    throw createError({
      message: 'Konnte Rollen oder Nutzerdaten nicht abrufen',
      cause: error,
      fatal: true,
    })
  }
}

if (userStore.isLoggedIn) {
  await healthCheckStore.doFullHealthCheck();
  await systemAnnouncementsStore.fetchSystemAnnouncements();

  // Set up basic global data
  try {
    await configStore.fetchAllConfigs();
    await drugDbUpdaterStore.fetchStatus();
    await studyStore.loadAvailableStudies();
    await drugFieldsStore.fetchFields();
    await drugFieldsStore.fetchCodes();

    // Update the status on a regular basis
    if (statusRefreshInterval.value) {
      clearInterval(statusRefreshInterval.value);
      statusRefreshInterval.value = null;
    }
    statusRefreshInterval.value = setInterval(refreshStatus, statusRefreshIntervalDelay);
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

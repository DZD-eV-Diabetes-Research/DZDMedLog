<script setup lang="ts">
const { $medlogapi } = useNuxtApp()
const drugFieldStore = useDrugFields();
const eventStore = useEventStore();
const interviewStore = useInterviewStore();
const userStore = useUserStore();
const studyStore = useStudyStore();

const logoutError = ref();

onMounted(async () => {
  try {
    await $medlogapi("/api/auth/logout", {
      method: 'POST'
    })
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

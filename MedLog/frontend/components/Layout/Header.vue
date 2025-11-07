<template>
  <header class="flex w-full bg-white py-4 px-10">
    <div class="flex w-full justify-between items-center mx-auto">
      <div>
        <NuxtLink
          class="text-4xl font-bold text-gray-800 hover:border-[#ec372d] hover:border-b-2" to="/"
          @click="resetStore">
          DZD Medlog
        </NuxtLink>
      </div>

      <div class="flex flex-col text-start justify-center">
        <p :class="userStore.userName ? 'text-gray-600' : 'invisible text-transparent'" class="text-lg">Benutzer: {{
          userStore.userName }}</p>
        <p :class="route.params.study_id ? 'text-gray-600' : 'invisible text-transparent'" class="text-lg">Studie: {{
          studyName }}</p>
        <p :class="probandID ? 'text-gray-600' : 'invisible text-transparent'" class="text-lg">ProbandenID:
          {{ probandID }}</p>
        <p :class="studyStore.event ? 'text-gray-600' : 'invisible text-transparent'" class="text-lg">Event: {{
          studyStore.event }}</p>
      </div>

      <div class="w-60">
        <img src="/img/logos/dzd.png" alt="DZD" class="max-w-full">
      </div>
    </div>
  </header>

  <div class="flex justify-between items-center px-10 py-2">
    <button
      v-if="showHeader"
      class="bg-white text-black border-2 border-black px-4 py-2 rounded-lg hover:bg-black hover:text-white hover:transition hover:duration-300"
      @click="logout()">Logout</button>

    <UBreadcrumb v-if="showHeader" :links="links" />

    <button
      v-if="showHeader"
      class="bg-white text-black border-2 border-black px-4 py-2 rounded-lg hover:bg-black hover:text-white hover:transition hover:duration-300"
      @click="navigateTo('manage/users')">Kontoverwaltung</button>
  </div>
</template>

<script setup>
import { ref, computed, watchEffect } from 'vue';

const userStore = useUserStore();
const studyStore = useStudyStore();
const route = useRoute();

const studyName = ref('');
const probandID = ref('');
const eventName = ref('');

watchEffect(async () => {
  if (route.params.study_id) {
    const study = await studyStore.getStudy(route.params.study_id);
    studyName.value = study ? study.display_name : 'Study not found';
    eventName.value = study?.event || '';
  } else {
    studyName.value = '';
    eventName.value = '';
  }
  probandID.value = route.params.proband_id || '';
});

watchEffect(async () => {
  if (!route.params.event_id) {
    studyStore.event = "";
    eventName.value = "";
  } else {
    eventName.value = studyStore.event;
  }
});

function logout() {
  userStore.$reset();
  studyStore.$reset();
  const {$medlogapi} = useNuxtApp();
  $medlogapi("/api/auth/logout", {
    method: 'POST'
  })
  const router = useRouter()
  router.push({ path: '/login' });
}


function resetStore() {
  studyStore.$reset();
}

const pathSegments = route.path.split('/').filter(Boolean);

const studyLabelEventVerwaltung = computed(() => `${studyName.value} Eventverwaltung`);
const studyLabelExport = computed(() => `${studyName.value} Export`);
const studyInterviewLabel = computed(() => `${studyName.value}: Proband ${route.params.proband_id}`);

const links = [{
  label: 'Home',
  icon: 'i-heroicons-home',
  to: '/',
}];

if (pathSegments.includes('studies')) {
  links.push({ label: 'Studien', to: '/studies' });

  const studiesIndex = pathSegments.indexOf('studies');

  if (pathSegments.includes('export')) {
    links.push({ label: studyLabelExport });
  }
  else if (studiesIndex + 1 < pathSegments.length) {

    links.push({ label: studyLabelEventVerwaltung });
  }
} else if (pathSegments.includes('interview')) {
  links.push({ label: 'Neue Interviews Starten', to: '/interview' });

  const probandIndex = pathSegments.indexOf('proband');
  const studyIndex = pathSegments.indexOf('study');
  const eventIndex = pathSegments.indexOf('event');

  if (probandIndex !== -1 && studyIndex !== -1) {
    links.push({ label: studyInterviewLabel, to: `/interview/proband/${route.params.proband_id}/study/${route.params.study_id}` });

    if (eventIndex !== -1) {
      links.push({ label: `Event ${eventName.value}`, to: null });
    }
  }
}

// Show logout buttion breadcrumbs and help only when not on "/"
const showHeader = computed(() => route.path !== '/login')

</script>

<style scoped>
header {
  box-shadow: inset 0 -0.3rem 0 #DA281C
}
</style>

<template>
  <header class="flex w-full  border-b-4 border-accent bg-white shadow-md py-4 px-10">
    <div class="flex w-full justify-between items-center mx-auto">
      <div>
        <NuxtLink class="text-4xl font-bold text-gray-800 hover:border-[#ec372d] hover:border-b-2" to="/user"
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
        <img src="/img/logos/dzd.png" alt="DZD" class="max-w-full" />
      </div>
    </div>
  </header>

  <div class="flex justify-between items-center px-10 py-2">
    <button v-if="tokenStore.loggedIn"
      class="bg-white text-black border-2 border-black px-4 py-2 rounded-lg hover:bg-black hover:text-white hover:transition hover:duration-300"
      @click="logout()">Logout</button>
      
    <UBreadcrumb v-if="tokenStore.loggedIn" :links="links" />
    
    <button v-if="tokenStore.loggedIn"
      class="bg-white text-black border-2 border-black px-4 py-2 rounded-lg hover:bg-black hover:text-white hover:transition hover:duration-300"
      @click="openSlide = true">Hilfe</button>
  </div>

  <!-- SLIDER INFO HELP -->
  <USlideover v-model="openSlide">

    <UCard class="flex flex-col flex-1"
      :ui="{ body: { base: 'flex-1' }, ring: '', divide: 'divide-y divide-gray-400 dark:divide-gray-800' }">
      <template #header>
        <h5 class="text-center text-2xl font-medium">How to use DZD-Medlog</h5>
      </template>
      <div>
        <h4 class="text-xl text-center">DZD-Medlog besteht im Kern aus 3 Komponenten</h4>
        <br>
        <p class="font-semibold">Teil 1: Studien und Interviews erstellen bzw. verwalten</p>
        <p class="font-semibold">Teil 2: Medikamente zu einem Interview hinzufügen</p>
        <p class="font-semibold">Teil 3: Daten einer Studie exportieren</p>
        <br>
        <p>Teil 1 finden Sie mittels des Buttons "Studienverwaltung" auf der Landingpage. Diese können Sie von überall
          erreichen, indem Sie auf den DZD-Medlog-Schriftzug in der oberen linken Ecke klicken.
          Bitte beachten Sie, dass nur Benutzer mit Admin-Rechten neue Studien und Interviews anlegen können.</p>
        <br>
        <p>Teil 2 wird über den Button "Interview durchführen" erreicht. Hier wird eine von Ihnen gewählte
          Probanden-ID verlangt. Nun sehen Sie eine Medikationsübersicht des Patienten über die gesamte Studie.
          Hier haben Sie die Möglichkeit, ein Interview durchzuführen oder zu bearbeiten.</p>
        <br>
        <p>Sie haben die Möglichkeit, über den Button
          "Medikationsübernahme"
          die Medikamente <strong>des letzten abgeschlossenen Events</strong> zu übernehmen.</p>
        <br>
        <p>Teil 3, den <strong>Datenexport</strong>, erreichen Sie, wie die Verwaltung der Studien, über den Button
          "Studienverwaltung" von
          der Landingpage aus.</p>
        <p>Des weiteren können Sie sich über die Breadcrumbs, am oberen Bildschirmrand, zu den jeweiligen vorher besuchten Seiten klicken</p>
        <br>
        <div id="zusatzinfo" class="flex flex-row mt-80">
          <p>Für Admins oder Technikinteressierte finden Sie hier unser <a
              class="text-blue-600 hover:border-b-2 hover:border-blue-600" href="https://www.github.com">Repository</a>
          </p>
        </div>
      </div>
      <template #footer>
        <div class="flex flex-col text-left text-sm space-y-1">
          <p>Wenn Sie Fragen oder Feedback haben, melden Sie sich gerne.</p>
          <p class="text-center">someEmail@someHost.com</p>
          <!-- <div class="flex flex-row items-center space-x-2 mt-2">
        <p>Oder besuchen Sie unsere GitHub-Seite: </p>
        <a href="https://www.github.com" target="_blank"><img src="/icons/github-mark.svg" alt="github-icon" class="w-6" /></a>
      </div> -->
        </div>
      </template>
    </UCard>


  </USlideover>
</template>

<script setup>
import { ref, computed, watchEffect } from 'vue';

const tokenStore = useTokenStore();
const userStore = useUserStore();
const studyStore = useStudyStore();
const probandStore = useProbandStore();
const router = useRouter();
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
  tokenStore.$reset();
  probandStore.$reset();
  router.push({ path: '/' });
}


function resetStore() {
  probandStore.$reset();
  studyStore.$reset();
}

const openSlide = ref(false)

const resetStores = () => {
  studyName.value = "";
  probandStore.probandID = "";
  studyStore.event = "";  
};

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
  links.push({ label: 'Studien', to: '/studies'});

  const studiesIndex = pathSegments.indexOf('studies');
  
  if (pathSegments.includes('export')) {
    links.push({ label: studyLabelExport });
  } 
  else if (studiesIndex + 1 < pathSegments.length) {
    
    links.push({ label: studyLabelEventVerwaltung});
  }
} else if (pathSegments.includes('interview')) {
  links.push({ label: 'Neues Interview', to: '/interview' });

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

</script>

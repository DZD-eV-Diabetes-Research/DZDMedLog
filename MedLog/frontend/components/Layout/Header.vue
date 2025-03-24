<template>
  <header class="flex w-full border-b-4 border-accent bg-white shadow-md p-4">
    <div class="flex w-full justify-between items-center max-w-5xl mx-auto">
      <div>
        <NuxtLink class="text-xl font-bold text-gray-800" to="/user" @click="resetStore">
          DZD Medlog
        </NuxtLink>
      </div>

      <div class="flex flex-col items-start space-y-1">
        <p v-if="userStore.userName" class="text-sm text-gray-600">User: {{ userStore.userName }}</p>
        <p v-if="route.params.study_id" class="text-sm text-gray-600">Study: {{ studyName }}</p>
        <p v-if="probandStore.probandID" class="text-sm text-gray-600">ProbandenID: {{ probandStore.probandID }}</p>
        <p v-if="studyStore.event" class="text-sm text-gray-600">Event: {{ studyStore.event }}</p>
      </div>

      <div class="w-40">
        <img src="/img/logos/dzd.png" alt="DZD" class="max-w-full" />
      </div>
    </div>
  </header>

  <div class="flex justify-end p-2 space-x-2">
    <button v-if="tokenStore.loggedIn" class="bg-red-500 text-white px-4 py-2 rounded" @click="logout()">Logout</button>
    <button v-if="tokenStore.loggedIn" :class="profileButtonClass" @click="toggelProfile()">
      {{ userStore.buttonText }}
    </button>
  </div>
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

watchEffect(async () => {
  if (route.params.study_id) {
    const study = await studyStore.getStudy(route.params.study_id);
    studyName.value = study ? study.display_name : 'Study not found';
  } else {
    studyName.value = '';
  }
});

function logout() {
  userStore.$reset();
  studyStore.$reset();
  tokenStore.$reset();
  probandStore.$reset();
  router.push({ path: '/' });
}

function toggelProfile() {
  userStore.toggle_profile();
}

function resetStore() {
  probandStore.$reset();
  studyStore.$reset();
}

const profileButtonClass = computed(() =>
  userStore.buttonText === 'Toggle to User' ? 'bg-green-500 text-white px-4 py-2 rounded' : 'bg-blue-500 text-white px-4 py-2 rounded'
);
</script>

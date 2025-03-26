<template>
  <header class="flex w-full  border-b-4 border-accent bg-white shadow-md py-4 px-10">
    <div class="flex w-full justify-between items-center mx-auto">
      <div>
        <NuxtLink class="text-4xl font-bold text-gray-800 hover:border-[#ec372d] hover:border-b-2" to="/user"
          @click="resetStore">
          DZD Medlog
        </NuxtLink>
      </div>

      <div class="flex flex-col items-start">
        <p :class="userStore.userName ? 'text-gray-600' : 'invisible text-transparent'" class="text-lg">Benutzer: {{
          userStore.userName }}</p>
        <p :class="route.params.study_id ? 'text-gray-600' : 'invisible text-transparent'" class="text-lg">Studie: {{
          studyName }}</p>
        <p :class="probandStore.probandID ? 'text-gray-600' : 'invisible text-transparent'" class="text-lg">ProbandenID:
          {{ probandStore.probandID }}</p>
        <p :class="studyStore.event ? 'text-gray-600' : 'invisible text-transparent'" class="text-lg">Event: {{
          studyStore.event }}</p>
      </div>

      <div class="w-60">
        <img src="/img/logos/dzd.png" alt="DZD" class="max-w-full" />
      </div>
    </div>
  </header>

  <div class="flex justify-between px-10 py-2">
    <button v-if="tokenStore.loggedIn"
      class="bg-white text-black border-2 border-black px-4 py-2 rounded-lg hover:bg-black hover:text-white hover:transition hover:duration-300"
      @click="logout()">Logout</button>
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
  userStore.buttonText === 'Toggle to User' ? 'bg-green-500 text-white px-4 py-2 rounded-lg' : 'bg-blue-500 text-white px-4 py-2 rounded-lg'
);
</script>

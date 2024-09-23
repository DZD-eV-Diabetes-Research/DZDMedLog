<template>
  <header class="nav">
    <div class="nav__content">
      <div>
        <div class="nav__title">
          <NuxtLink class="anchor" to="/user" @click="resetStore">
            DZD Medlog
          </NuxtLink>
        </div>
      </div>
      <div class="activeStudy-container">
        <div class="activeStudy">
          <p :class="{ invisible: !userStore.userName }" class="flex-item">Benutzer: {{ userStore.userName }}</p>
          <p :class="{ invisible: !route.params.study_id }" class="flex-item">Studie: {{ studyName }}</p>
          <p :class="{ invisible: !probandStore.probandID }" class="flex-item">ProbandenID: {{ probandStore.probandID }}</p>
          <p :class="{ invisible: studyStore.event === '' }" class="flex-item">Event: {{ studyStore.event }}</p>
        </div>
      </div>
      <div class="nav__logo">
        <img src="/img/logos/dzd.png" alt="DZD" />
      </div>
    </div>
  </header>
  <div class="button-container">
    <div class="logout_button">
    <UIBaseButton v-if="tokenStore.loggedIn" @click="logout()">Logout</UIBaseButton>
  </div>
  <div class="profile_button">
    <UIBaseButton v-if="tokenStore.loggedIn" @click="toggelProfile()">{{ userStore.buttonText }}</UIBaseButton>
  </div>
  </div>
</template>

<script setup>
import { ref, watchEffect } from 'vue';

const tokenStore = useTokenStore();
const userStore = useUserStore();
const studyStore = useStudyStore();
const probandStore = useProbandStore()
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
  userStore.$reset()
  studyStore.$reset()
  tokenStore.$reset()
  probandStore.$reset()
  router.push({ path: "/" })
}

function toggelProfile() {
  userStore.toggle_profile()
}
// function toggelProfile() {
//   userStore.toggle_profile()
//   if (userStore.buttonText === "Back") {
//     router.push({ path: "/profile" })
//   } else {
//     router.go(-1)
//   }
// }

function resetStore() {
  probandStore.$reset()
  studyStore.$reset()
}


const profileButtonClass = computed(() => {
  let baseClass = 'profile_button'
  if (userStore.buttonText === 'Toggle to User') {
    return `${baseClass} toggle_to_user`
  } else {
    return `${baseClass} toggle_to_admin`
  }
})

</script>

<style lang="scss" scoped>
@import "../../assets/mixins";
@import "../../assets/variables/breakpoints";

.anchor {
  color: #20282D;
  margin-top: var(--space-4);
  font-family: var(--font-family-heading);
  font-weight: var(--font-weight-heading, inherit);
  text-transform: var(--text-transform-heading, inherit);
  -webkit-hyphens: auto;
  hyphens: auto;
  letter-spacing: var(--letter-spacing-heading, inherit);
  line-height: 1.2;
  padding: 2rem;
}

.nav {
  display: flex;
  width: 100%;
  border-bottom: 10px solid var(--accent);
  position: relative;
}

.nav__content {
  @include container();
  margin: 0;
  padding: var(--space-4) var(--layout-padding-x);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: flex-start;
  height: var(--nav-height);
  pointer-events: auto;
  transition: height var(--transition-long), background var(--transition-long);
  position: relative;
  z-index: 3;
  background-color: var(--nav-bg-color);
  gap: var(--space-4);
  width: 100%;

  @include breakpoint(md) {
    flex-direction: row;
    align-items: center;
  }
}

.nav__title {
  font-size: var(--font-size-2xl);
  font-weight: 800;
  color: var(--primary12);

  .router-link-custom {
    font-size: inherit;
    font-weight: inherit;
    text-decoration: none;
    color: inherit;
  }
}

.nav__logo {
  width: 200px;
  order: -1;
  padding-right: 2rem;

  @include breakpoint(md) {
    order: inherit;
  }

  img {
    max-width: 100%;
  }
}

.button-container {
  display: flex;
  align-items: center;
  margin-top: 0.25rem;
  margin-right: 0.25rem;
  margin-left: 0.25rem;
}

.logout_button {
  margin-right: auto;
}

.profile_button {
  margin-left: auto;
}

.about {
  padding: var(--space-6);
}

.fixed-size {
  height: 24px;
  width: 500px;
}

.invisible {
  visibility: hidden;
}

.activeStudy-container {
  display: flex;
  justify-content: center;
  flex: 1; 
  padding: 1rem;
}

.activeStudy {
  display: flex;
  flex-direction: column; 
  align-items: flex-start; 
  gap: -10px; 
  width: 500px; 
  margin-left: 125px;
}

.flex-item {
  height: 27px; 
  width: 100%; 
  white-space: nowrap; 
  overflow: hidden; 
  text-overflow: ellipsis;
}
</style>

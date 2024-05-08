<template>
  <header class="nav">
    <div class="nav__content">
      <div>
        <div class="nav__title">
          <RouterLink @click="reset_profile_button" to="/" class="router-link-custom">DZD MedLog</RouterLink>
        </div>
        <div class="nav__subtitle">
          Your trustworthy medication logging page
        </div>
      </div>
      <div class="nav__logo">
        <img src="/img/logos/dzd.png" alt="DZD">
      </div>
    </div>
  </header>
  <div class="button-container">
    <button class="logout_button" v-if="tokenStore.loggedStatus" @click="logout">Logout</button>
    <button class="profile_button" v-if="tokenStore.loggedStatus" @click="my_profile">{{userStore.buttonText}}</button>
  </div>
</template>

<script>

import { useUserStore } from '@/stores/UserStore'
import { useTokenStore } from '@/stores/TokenStore'
import { RouterLink } from 'vue-router';

export default {
  name: "Header",
  setup() {
    const userStore = useUserStore()
    const tokenStore = useTokenStore()
    return { userStore, tokenStore }
  },
  methods: {
    reset_profile_button(){
      this.userStore.buttonText= "Profile"
      this.userStore.viewProfile = false
      this.userStore.userMe()
    },
    logout() {
      this.userStore.$reset()
      this.tokenStore.$reset()
      this.$router.push("/")
    },
    my_profile() {
      this.userStore.toggle_profile()
      if(this.userStore.buttonText === "Back"){
        this.$router.push("/profile")
      } else {
        this.$router.go(-1)
      }
    }
  }
};


</script>
<style lang="scss">
@import "../../styles/mixins";
@import "../../styles/variables/breakpoints";

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
</style>

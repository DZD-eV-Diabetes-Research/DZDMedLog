<template>
  <header class="nav">
    <div class="nav__content">
      <div>
        <div class="nav__title">DZD MedLog</div>
        <div class="nav__subtitle">
          Your trustworthy medication logging page
        </div>
      </div>
      <div class="nav__logo">
        <img src="/img/logos/dzd.png" alt="DZD">
      </div>
    </div>
  </header>
  <button v-if="tokenStore.get_logged_in" @click="logout">Logout</button>
</template>

<script>

import { useUserStore } from '@/stores/UserStore'
import { useTokenStore } from '@/stores/TokenStore'

export default {
  name: "Header",
  setup() {
        const userStore = useUserStore()
        const tokenStore = useTokenStore()
        return { userStore, tokenStore}
    },

    methods: {
      logout() {
            this.userStore.$reset()
            this.tokenStore.$reset()
            this.$router.push("/")
        },
}};


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

.button {
  margin-left: auto;
}

.about {
  padding: var(--space-6);
}</style>

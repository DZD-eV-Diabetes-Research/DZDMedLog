<template>
  <header class="nav">
    <div class="nav__content">
      <div>
        <div class="nav__title">
          <a @click="back" class="anchor" href="/">DZD Medlog</a>
        </div>
        <div class="nav__subtitle">
          Your trustworthy medication logging page
        </div>
      </div>
      <div class="nav__logo">
        <img src="/img/logos/dzd.png" alt="DZD" />
      </div>
    </div>
  </header>
  <div class="button-container">
    <button class="logout_button" v-if="tokenStore.loggedIn" @click="logout()">Logout</button>
    <button class="profile_button" v-if="tokenStore.loggedIn" @click="my_profile()">{{userStore.buttonText}}</button>
  </div>
</template>

<script setup>
const tokenStore = useTokenStore();
const userStore = useUserStore();
const router = useRouter()

function logout() {
      this.userStore.$reset()
      this.tokenStore.$reset()
      router.push({ path: "/" })
}

function my_profile() {
      userStore.toggle_profile()
      if(userStore.buttonText === "Back"){
        router.push({ path: "/profile" })
      } else {
        router.go(-1)
      }
    }

function back() {
  const router = useRouter()
  router.push({ path: "/" })
}

</script>

<style lang="scss" scoped>
@import "../../assets/mixins";
@import "../../assets/variables/breakpoints";

.anchor{  
  color: #20282D;
  margin-top: var(--space-4);
  font-family: var(--font-family-heading);
  font-weight: var(--font-weight-heading, inherit);
  text-transform: var(--text-transform-heading, inherit);
  -webkit-hyphens: auto;
  hyphens: auto;
  letter-spacing: var(--letter-spacing-heading, inherit);
  line-height: 1.2;
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

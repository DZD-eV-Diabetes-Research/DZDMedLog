<template>
  <Header />

  <div class="layout">
    <div class="layout__content">

      <section class="about">
        <h2>About</h2>
        <p>
          A web-based tool to log your patients medication
        </p>

        <h2>How-to</h2>
        <p>
          Log in with your DZD-Login and start entering data
        </p>
      </section>

      <slot />
    </div>
  </div>
  <Footer />
</template>
<script>
  import Footer from './Footer.vue';
  import Header from './Header.vue';
  export default {
    name: 'Layout',
    components: {
      Footer, Header,
    }
  }
</script>
<style lang="scss">
  .layout {
    padding-top: 0 !important;
  }
</style>
<template>
    <Header />
  
    <div class="layout">
      <div class="layout__content">
  
        <section class="about" v-if="showAbout">
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
  
  <script setup lang="ts">
  import { ref } from 'vue';
  import Footer from './Footer.vue';
  import Header from './Header.vue';
  
  const showAbout = ref(false);
  </script>
  
  <style lang="scss">
    .layout {
      padding-top: 0 !important;
    }
  </style>
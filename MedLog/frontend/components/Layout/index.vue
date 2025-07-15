<template>
  <Header />
      <slot />
  <Footer />
</template>

<script setup lang="ts">
import Footer from './Footer.vue';
import Header from './Header.vue';
</script>
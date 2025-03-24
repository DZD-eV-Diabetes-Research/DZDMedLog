<template>
  <Header />

  <div class="pt-0">
    <div class="max-w-5xl mx-auto p-4">
      <section v-if="showAbout" class="bg-gray-100 p-6 rounded-lg shadow-md">
        <h2 class="text-xl font-semibold">About</h2>
        <p class="text-gray-600">A web-based tool to log your patients' medication</p>

        <h2 class="text-xl font-semibold mt-4">How-to</h2>
        <p class="text-gray-600">Log in with your DZD-Login and start entering data</p>
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
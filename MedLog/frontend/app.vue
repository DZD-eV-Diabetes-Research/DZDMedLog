<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>

<script setup lang="ts">
useHead({
  title: 'DZD Medlog',
  meta: [
    { name: 'description', content: 'DZD Webapp to audit medication for clinical studies' }
  ],
})
</script>
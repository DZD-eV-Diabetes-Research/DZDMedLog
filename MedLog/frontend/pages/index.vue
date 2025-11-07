<template>
  <UIBaseCard style="text-align:center">
    <h3 class="text-4xl font-medium my-4">Hello {{userStore.userName}}</h3>
    <div class="flex flex-col space-y-10 my-10 items-center">
      <button class="text-xl font-light outline outline-1 outline-black hover:outline-2 hover:shadow-xl rounded-lg py-2 px-4" @click="conductInterview()">Interview durchführen</button>
      <button class="text-xl font-light outline outline-1 outline-black hover:outline-2 hover:shadow-xl rounded-lg py-2 px-4" @click="showStudies()">Studien Verwaltung</button>
    </div>
  </UIBaseCard>
</template>

<script setup lang="ts">

const userStore = useUserStore()

async function conductInterview() {
    await navigateTo("/interview");
}

async function showStudies() {
    await navigateTo("/studies");
}

</script>

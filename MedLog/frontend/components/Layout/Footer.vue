<template>
  <footer class="bg-gray-100 w-full py-4 mt-6">
    <div class="flex justify-end items-center py-2 px-10 mx-auto">
      <div>
        <NuxtLink to="/help">Hilfe</NuxtLink>
        <NuxtLink to="https://www.dzd-ev.de/impressum" :external="true" target="_blank">Impressum</NuxtLink>
      </div>
    </div>
  </footer>
</template>

<style scoped>
a ~ a {
  margin-left: 0.7rem;
}
</style>

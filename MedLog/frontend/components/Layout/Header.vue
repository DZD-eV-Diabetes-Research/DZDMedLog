<template>
  <header class="flex flex-col w-full bg-white py-4 px-10">
    <div class="flex w-full justify-between items-center gap-20">
      <div>
        <NuxtLink to="/" class="text-4xl font-bold text-gray-800 hover:border-[#ec372d] hover:border-b-2">
          {{ configStore.appName }}
        </NuxtLink>
      </div>

      <div class="w-60">
        <img src="/img/logos/dzd.png" alt="DZD-Logo" class="max-w-full">
      </div>
    </div>

    <UHorizontalNavigation :links="menuItems" class="mt-4" />
  </header>
</template>

<script setup>
import { computed } from '#imports';

const configStore = useConfigStore();
const userStore = useUserStore();

const menuItems = computed(() => {
  const links = [
    [{
      label: 'Interview durchführen',
      labelClass: 'text-base',
      icon: 'i-heroicons-home',
      to: '/'
    }]
  ];

  const rightSideLinks = [];

  if (userStore.isLoggedIn && userStore.isAdmin) {
    rightSideLinks.push({
      label: 'Studienverwaltung',
      labelClass: 'text-base',
      icon: 'i-heroicons-clipboard-document-list',
      to: '/manage/studies'
    });
  }

  if (userStore.isLoggedIn && userStore.isUserAdmin) {
    rightSideLinks.push({
      label: 'Kontoverwaltung',
      labelClass: 'text-base',
      icon: 'i-heroicons-users',
      to: '/manage/users'
    });
  }

  rightSideLinks.push({
    label: 'Hilfe',
    labelClass: 'text-base',
    icon: 'i-heroicons-question-mark-circle',
    to: '/help',
  });

  if (userStore.isLoggedIn) {
    rightSideLinks.push({
      label: 'Logout',
      labelClass: 'text-base',
      icon: 'i-heroicons-power',
      to: '/logout'
    });
  } else {
    rightSideLinks.push({
      label: 'Login',
      labelClass: 'text-base',
      icon: 'i-heroicons-arrow-right-end-on-rectangle',
      to: '/login',
    });
  }

  links.push(rightSideLinks);

  return links;
});
</script>

<style scoped>
header {
  box-shadow: inset 0 -0.3rem 0 #DA281C
}
</style>

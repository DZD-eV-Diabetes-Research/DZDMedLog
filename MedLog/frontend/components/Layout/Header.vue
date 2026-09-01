<template>
  <header class="flex flex-col w-full bg-white py-4 px-10">
    <div class="grid grid-cols-1 md:grid-cols-3 py-2">
      <div class="text-start">
        <NuxtLink to="/" class="text-2xl lg:text-4xl font-bold text-gray-800 hover:border-[#ec372d] hover:border-b-2">
          {{ configStore.appName }}
        </NuxtLink>
      </div>

      <div class="text-center justify-self-center">
        <SystemAnnouncements />
      </div>

      <div class="text-end justify-self-end">
        <img src="/img/logos/dzd.png" alt="DZD-Logo" class="max-w-40 lg:max-w-60">
      </div>
    </div>

    <div class="flex items-center mt-4">
      <UHorizontalNavigation :links="menuItems" class="flex-1" />
      <UDropdown
        v-if="userStore.isLoggedIn"
        :items="userMenuItems"
        :popper="{ placement: 'bottom-end' }"
      >
        <UButton
          class="group text-base py-3.5 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
          color="gray"
          variant="ghost"
          icon="i-heroicons-user-circle"
          trailing-icon="i-heroicons-chevron-down-20-solid"
          :label="currentUserDisplayName"
          :ui="{icon: { base: 'text-gray-400 dark:text-gray-500 group-hover:text-gray-700 dark:group-hover:text-gray-200'}}"
        />
      </UDropdown>
    </div>
  </header>
</template>

<script setup>
import { computed } from '#imports';

const configStore = useConfigStore();
const studyPermissionStore = useStudyPermissionStore();
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

  if (userStore.isLoggedIn && (userStore.isAdmin || studyPermissionStore.currentUserCanManageSomeStudy)) {
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

  if (!userStore.isLoggedIn) {
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

const currentUserDisplayName = computed(() =>
  userStore.currentUser?.display_name ?? userStore.currentUser?.user_name ?? ''
);

const userMenuItems = computed(() => [[
  {
    label: 'Logout',
    labelClass: 'text-base',
    icon: 'i-heroicons-power',
    to: '/logout',
  },
]]);
</script>

<style scoped>
header {
  box-shadow: inset 0 -0.3rem 0 #DA281C
}
</style>

<template>
    <UCard :ui="{ ring: '', divide: 'divide-y divide-gray-100 dark:divide-gray-800' }">
        <template #header>
            <div class="my-3 space-y-2">
                <h1 class="text-center text-3xl">Medlog Einstellungen</h1>
                <h3 class="text-center text-xl">Userverwaltung</h3>
            </div>
        </template>

        <!-- <p>{{ users }}</p> -->

        <!-- <template #footer>
            <p>footer</p>
        </template> -->
    </UCard>
</template>

<script setup lang="ts">
// const tokenStore = useTokenStore();
// const runtimeConfig = useRuntimeConfig();


// const { data: users } = await useFetch(`${runtimeConfig.public.baseURL}user`, {
//     method: "GET",
//     headers: { 'Authorization': "Bearer " + tokenStore.access_token },
// })

// for (const user of users.items) {
//     console.log(user);
    
// }

// const columns = [{
//     key: 'user_name',
//     label: 'Benutzername'
// }, {
//     key: 'email',
//     label: 'Email'
// }, {
//     key: 'Angezeigter Name',
//     label: 'display_name'
// }, {
//     key: 'roles',
//     label: 'Rollen'
// }, {
//     key: 'actions'
// }]




</script>
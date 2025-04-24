<template>
    <UCard :ui="{ ring: '', divide: 'divide-y divide-gray-100 dark:divide-gray-800' }">
        <template #header>
            <div class="my-3 space-y-2">
                <h1 class="text-center text-3xl">Medlog Einstellungen</h1>
                <h3 class="text-center text-xl">Userverwaltung</h3>
            </div>
        </template>

        <div v-if="mappedUsers">
            <UTable v-model:expand="expand" :rows="mappedUsers" :columns="columns">

                <template #roles-data="{ row }">
                    <div v-if="row.roles.length > 0" class="space-x-2" >
                        <UBadge class="bg-white text-slate-500 border-2 border-slate-500 px-2 py-1 rounded-lg" v-for="role in row.roles">{{ role }}</UBadge>
                    </div>
                    <div v-else>

                    </div>
                </template>

                <template #expand="{ row }">
                    <div class="flex flex-col p-4 bg-gray-50 rounded text-center items-center space-y-3">
                        <p v-if="row.roles.length > 0">{{ row.user_name }} sind folgenden Rollen zugewiesen: </p>
                        <p v-else>{{ row.user_name }} sind aktuell keinen Rollen zugewiesen</p>
                        <div class="space-y-2 mb-20">
                            <UCheckbox v-for="role in roles" :key="role.role_name"
                                v-model="selectedRolesPerUser[row.id]" :value="role.role_name" :name="role.role_name"
                                :label="role.role_name" />
                        </div>
                        <div class="mt-4">
                            <UButton @click="patchUser(row.id)"
                                class="bg-white text-slate-500 border-2 border-slate-500 px-2 py-1 rounded-lg hover:bg-slate-500 hover:text-white">
                                Speichern</UButton>
                        </div>
                    </div>
                </template>

                <template #expand-action="{ row }">
                    <UButton v-if="row.hasExpand" @click="handleToggle(row)"
                        class="bg-white text-slate-500 border-2 border-slate-500 px-2 py-1 rounded-lg hover:bg-slate-500 hover:text-white">
                        {{ isExpanded ? 'Zuklappen' : 'Bearbeiten' }}
                    </UButton>
                </template>
            </UTable>
        </div>
        <div v-else>
            Loading
        </div>
        <div class="text-center">
            <hr class="my-8 border-2">
            <h2 class="text-3xl font-semibold mb-4">Aktuelle Rollen</h2>
            <div class="flex flex-row justify-center mb-4" v-for="role in roles">
                <p><span class="font-bold">{{ role.role_name }}</span>: {{ role.description }}</p>
            </div>
        </div>
    </UCard>
</template>

<script setup lang="ts">
const tokenStore = useTokenStore();
const runtimeConfig = useRuntimeConfig();
const { $api } = useNuxtApp();


const { status, data: users, refresh } = useAPI(`${runtimeConfig.public.baseURL}user`, {
    method: "GET",
})

const { data: roles } = useAPI(`${runtimeConfig.public.baseURL}role`, {
    method: "GET",
})


const mappedUsers = computed(() => {
    if (!users.value) return [];
    return users.value.items.map(user => ({
        id: user.id,
        user_name: user.user_name,
        email: user.email,
        display_name: user.display_name,
        roles: user.roles,
        hasExpand: true
    }))
})

const columns = [{
    key: 'user_name',
    label: 'Benutzername'
}, {
    key: 'email',
    label: 'Email'
}, {
    key: 'display_name',
    label: 'Angezeigter Name'
}, {
    key: 'roles',
    label: 'Rollen'
}, {
    key: 'actions'
}]

const currentUser = ref()

const patchUser = async function (id: string) {
    try {
        const patchBody = { "roles": selectedRolesPerUser.value[id] }
        await $api(
            `${runtimeConfig.public.baseURL}user/${id}`,
            {
                method: "PATCH",
                body: patchBody,
            }
        );
        await refresh()
        expand.value.openedRows = []
    } catch (error) {
        console.log(error);

    }
}

const expand = ref({
    openedRows: [],
    row: {}
})

function isRowExpanded(row: any) {
    return expand.value.openedRows.some((r) => r.id === row.id)
}

function handleToggle(row: any) {
    currentUser.value = row
    const alreadyOpen = isRowExpanded(row)
    expand.value.openedRows = alreadyOpen ? [] : [row]
    selectedRolesPerUser.value[row.id] = [...row.roles]
}

const selectedRolesPerUser = ref<Record<string, string[]>>({})

</script>

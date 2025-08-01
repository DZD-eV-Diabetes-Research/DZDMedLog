<!-- This component deals with the study-permission-management that can be found at the study level -->

<template>
    <UCard :ui="{ ring: '', divide: 'divide-y divide-gray-100 dark:divide-gray-800' }">
        <template #header>
            <div class="my-3 space-y-2">
                <h1 class="text-center text-3xl">Studien Einstellungen</h1>
                <h3 class="text-center text-xl">Studien-Zugriffsrechte</h3>
            </div>
        </template>
        <div v-if="mappedUsers">
            <UTable v-model:expand="expand" :rows="mappedUsers" :columns="columns">
                <template #permissions-data="{ row }">
                    <div v-if="row.permissions.length > 0" class="space-x-2">
                        <UBadge v-for="permission in row.permissions" :key="permission"
                            class="bg-white text-slate-500 border-2 border-slate-500 px-2 py-1 rounded-lg">
                            {{ permission }}
                        </UBadge>
                    </div>
                    <div v-else>

                    </div>
                </template>

                <template #expand="{ row }">
                    <div class="flex flex-col p-4 bg-gray-50 rounded text-center items-center space-y-3">
                        <p v-if="row.permissions.length > 0">{{ row.userName }} sind folgenden Zugriffsrechte
                            zugewiesen: </p>
                        <div class="space-y-2 mb-20">
                            <UCheckbox v-for="permission in permissionLabels" :key="permission"
                                v-model="selectedPermissionsPerUser[row.id]" :value="permission" :name="permission"
                                :label="permission" />
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
            <h2 class="text-3xl font-semibold mb-4">Aktuelle Zugriffsrechte</h2>
            <div class="flex flex-row justify-center mb-4" v-for="permission in permissions">
                <p><span class="font-bold">{{ permission.study_permission_name }}</span>: {{ permission.description }}
                </p>
            </div>
        </div>
    </UCard>
</template>

<script setup lang="ts">
const { $medlogapi } = useNuxtApp();
import { useMedlogapi } from '#imports';

//props

const props = defineProps<{
    studyId: string
}>()

// Api calls

const { data: permissions } = useMedlogapi('/api/study/permissions/available', {
    method: "GET"
})


const { data: users, refresh: permissionsRefresh } = useMedlogapi('/api/study/{study_id}/permissions', {
    path: {
        study_id: props.studyId,
    },
    method: "GET",

})


// Template preparation

// Here we alter the user array to a new form (mappedUsers2) to visualize them in the template

const permissionLabels = ["Study Viewer", "Study Interviewer", "Study Admin"];

const mappedUsers = computed(() => {
    if (!users.value) return [];
    return users.value.items.map(user => ({
        id: user.id,
        userName: user.user_ref.user_name,
        email: user.user_ref.email,
        displayName: user.user_ref.display_name,
        permissions: [user.is_study_viewer, user.is_study_interviewer, user.is_study_admin].map((value, index) => value ? permissionLabels[index] : null).filter(Boolean),
        hasExpand: true
    }))
})

const columns = [{
    key: 'userName',
    label: 'Benutzername'
}, {
    key: 'email',
    label: 'Email'
}, {
    key: 'displayName',
    label: 'Angezeigter Name'
}, {
    key: 'permissions',
    label: 'Zugriffsrechte'
}, {
    key: 'actions'
}]

const expand = ref({
    openedRows: [],
    row: {}
})

const currentUser = ref()

function isRowExpanded(row: any) {
    return expand.value.openedRows.some((r) => r.id === row.id)
}

function handleToggle(row: any) {
    currentUser.value = row
    const alreadyOpen = isRowExpanded(row)
    expand.value.openedRows = alreadyOpen ? [] : [row]
    selectedPermissionsPerUser.value[row.id] = [...row.permissions]
}

const selectedPermissionsPerUser = ref<Record<string, string[]>>({})

// Update users to the backend

const patchUser = async function (id: string) {
    try {
        const putBody = {
            "is_study_viewer": selectedPermissionsPerUser.value[id].includes("Study Viewer") ? true : false,
            "is_study_interviewer": selectedPermissionsPerUser.value[id].includes("Study Interviewer") ? true : false,
            "is_study_admin": selectedPermissionsPerUser.value[id].includes("Study Admin") ? true : false
        }

        await $medlogapi(
            '/api/study/{study_id}/permissions/{user_id}',
            {
                method: "PUT",
                body: putBody,
                path: {
                    study_id: props.studyId,
                    user_id: id
                }
            }
        );
        await permissionsRefresh()
        expand.value.openedRows = []
    } catch (error) {
        console.log(error);

    }
}
</script>
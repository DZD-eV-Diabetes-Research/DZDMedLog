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
                        <div class="space-y-2">
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

                <template #delete-data="{ row }">
                    <UButton icon="i-heroicons-trash"
                        class="bg-white text-slate-500 border-2 border-slate-500 px-2 py-1 rounded-lg hover:bg-slate-500 hover:text-white"
                        @click="deleteModal(row)" />
                </template>
            </UTable>
            <UModal v-model="openDeleteModal">
                <div class="p-4 text-center">
                    <h3 class="text-lg text-red-500">
                        Möchten Sie {{ currentUser.userName || "" }} wirklich löschen?
                    </h3>
                    <div class="flex justify-center space-x-2 mt-4">
                        <UButton color="gray" variant="soft" @click="openDeleteModal = false">Abbrechen</UButton>
                        <UButton color="red" @click="deletePermissions(currentUser.id)">Löschen</UButton>
                    </div>
                </div>
            </UModal>
            <div>
                <hr class="my-6 border-1">
                <div class="flex flex-col justify-center space-y-4">
                    <h3 class="text-center text-xl">Zugriffsrechte hinzufügen</h3>
                    <div v-if="no_permission_user_list.length > 0" class="flex flex-col justify-center space-y-4">
                        <USelect v-model="no_permission_user_id" :options="no_permission_user_list"
                            option-attribute="user_name" value-attribute="id" class="mx-auto" />
                        <div class="flex flex-row items-center justify-center space-x-4">
                            <UCheckbox v-for="permission in permissionLabels" :key="permission"
                                v-model="new_user_permissions" :value="permission" :name="permission"
                                :label="permission" />
                        </div>
                        <UButton type="submit" @click="patchUser(no_permission_user_id, new_user_permissions)"
                            label="Zugriffsrechte hinzufügen" color="violet" variant="soft"
                            class="border border-violet-500 hover:bg-violet-300 hover:border-white hover:text-white px-4 mx-auto" />
                    </div>
                    <div v-else>
                        <h3 class="text-center text-lg">Es gibt aktuell keine Nutzer ohne Zugriffsrechte</h3>
                    </div>
                </div>
            </div>
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


const { data: current_users, refresh: permissionsRefresh } = await useMedlogapi('/api/study/{study_id}/permissions', {
    path: {
        study_id: props.studyId,
    },
    method: "GET",

})

const { data: all_users, refresh: allUserRefresh } = await useMedlogapi('/api/user', {
    method: "GET",
})

const permission_id_list = computed(() =>
    current_users.value?.items.map((item) => item.user_id) ?? []
)

const no_permission_user_list = computed(() =>
    all_users.value?.items.filter(item => !permission_id_list.value.includes(item.id)) ?? []
)

const no_permission_user_id = ref(no_permission_user_list.value[0]?.id ?? null)

watch(no_permission_user_list, (newList) => {
    if (newList.length > 0) {
        no_permission_user_id.value = newList[0].id
    }
})


const new_user_permissions = ref([])


// Template preparation

// Here we alter the user array to a new form (mappedUsers2) to visualize them in the template

const permissionLabels = ["Study Viewer", "Study Interviewer", "Study Admin"];

const mappedUsers = computed(() => {
    if (!current_users.value) return [];
    return current_users.value.items.map(user => ({
        id: user.user_ref.id,
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
}, {
    key: 'delete'
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

// error messag if no permission is selected

// Update current_users to the backend

const patchUser = async function (id: string, permission_list?: Array<string>) {
    try {
        const list = permission_list !== undefined
            ? permission_list
            : selectedPermissionsPerUser.value[id];

        const putBody = {
            is_study_viewer: list.includes("Study Viewer"),
            is_study_interviewer: list.includes("Study Interviewer"),
            is_study_admin: list.includes("Study Admin")
        };


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
        await allUserRefresh()
        new_user_permissions.value = []
        expand.value.openedRows = []
    } catch (error) {
        console.log(error);

    }
}

const openDeleteModal = ref(false)
const deleteModal = async function (row: any) {
    currentUser.value = row
    openDeleteModal.value = true
}

const deletePermissions = async function (id: string) {
    await $medlogapi(
        '/api/study/{study_id}/permissions/{user_id}',
        {
            method: "DELETE",
            path: {
                study_id: props.studyId,
                user_id: id
            }
        }
    );
    await permissionsRefresh()
    await allUserRefresh()
    openDeleteModal.value = false
}

</script>
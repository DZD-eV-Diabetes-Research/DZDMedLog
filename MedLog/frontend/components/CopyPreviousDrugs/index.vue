<template>
    <div class="flex flex-col justify-center items-center">
        <div class="flex flex-row justify-center">
            <UButton @click="openCopyIntakeModal()" label="Medikation Übernehmen" color="green" variant="soft"
                style="margin-right: 10px"
                class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
            <div class="flex items-center ">
                <UTooltip :delay-duration="0" text="Medikatmente aus dem letzten Events übernehmen">
                    <UIcon name="i-heroicons-question-mark-circle" class="size-5" />
                </UTooltip>
            </div>
        </div>
        <UModal v-model="copyPreviousIntakesModal" class="custom-modal">
            <div class="p-10 text-center max-w-5xl">
                <div v-if="previousIntakes">
                    <UTable v-model="selected" :rows="people" @row-click="handleRowClick"/>
                    {{ selected }}
                    <UButton @click="test()" label="Medikation Übernehmen" color="green" variant="soft"
                        style="margin-right: 10px"
                        class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white  mt-4" />
                </div>
                <div v-if="!previousIntakes && !errorMessage">
                    loading
                </div>
                <div v-if="errorMessage">
                    <h3 class="text-red-500">Es gab ein Problem beim Laden der Medikamente. Bitte melden Sie sich bei
                        ihrem Admin</h3>
                </div>
            </div>
        </UModal>
    </div>
</template>

<script setup lang="ts">

const runtimeConfig = useRuntimeConfig();
const tokenStore = useTokenStore();
const route = useRoute();

const copyPreviousIntakesModal = ref(false)
const previousIntakes = ref()
const errorMessage = ref(false)

async function openCopyIntakeModal() {
    copyPreviousIntakesModal.value = true
    errorMessage.value = false
    try {
        //`${runtimeConfig.public.baseURL}study/${route.params.study_id}/proband/${route.params.proband_id}/interview/current/intake`
        const intakes = await $fetch(`${runtimeConfig.public.baseURL}study/b6f2c61b-d388-4412-8c9a-461ece251116/proband/1234/interview/current/intake`, {
            method: "GET",
            headers: { 'Authorization': "Bearer " + tokenStore.access_token },
        })

        previousIntakes.value = intakes

    } catch (error) {
        console.log(error);
        errorMessage.value = true
    }
}

function test() {
    console.log("speichert");
    copyPreviousIntakesModal.value = false
}

function handleRowClick(row: any) {
    const index = selected.value.findIndex(item => item.id === row.id);
    if (index === -1) {
        // Add to selection if not already selected
        selected.value.push(row);
    } else {
        // Remove from selection if already selected
        selected.value.splice(index, 1);
    }
}

const people = [{
    id: 1,
    name: 'Lindsay Walton',
    title: 'Front-end Developer',
    title1: 'Front-end Developer',
    title2: 'Front-end Developer',
    email: 'lindsay.walton@example.com',
    role: 'Member'
}, {
    id: 2,
    name: 'Courtney Henry',
    title: 'Designer',
    title1: 'Designer',
    title2: 'Designer',
    email: 'courtney.henry@example.com',
    role: 'Admin'
}, {
    id: 3,
    name: 'Tom Cook',
    title: 'Director of Product',
    title1: 'Director of Product',
    title2: 'Director of Product',
    email: 'tom.cook@example.com',
    role: 'Member'
}, {
    id: 4,
    name: 'Whitney Francis',
    title: 'Copywriter',
    title1: 'Copywriter',
    title2: 'Copywriter',
    email: 'whitney.francis@example.com',
    role: 'Admin'
}, {
    id: 5,
    name: 'Leonard Krasner',
    title: 'Senior Designer',
    title1: 'Senior Designer',
    title2: 'Senior Designer',
    email: 'leonard.krasner@example.com',
    role: 'Owner'
}, {
    id: 6,
    name: 'Floyd Miles',
    title: 'Principal Designer',
    title1: 'Principal Designer',
    title2: 'Principal Designer',
    email: 'floyd.miles@example.com',
    role: 'Member'
}]

const selected = ref([people[1]])

</script>
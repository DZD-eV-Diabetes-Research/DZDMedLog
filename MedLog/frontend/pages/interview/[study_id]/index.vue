<template>
    <Layout>
        <UIBaseCard @click="newInterview(item)" v-for="item in reversedEvents" style="text-align: center">
            <h3>{{ useStringDoc(item.name) }}</h3>
        </UIBaseCard>
        <UIBaseCard v-if="userStore.isAdmin" class="noHover">
            <UButton @click="showModal = true" label="Event anlegen" color="green" variant="soft"
                class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
            <UModal v-model="showModal">
                <div class="p-4" style="text-align: center;">
                    <UForm :schema="schema" :state="state" class="space-y-4" @submit="createEvent">
                        <h3>Event anlegen</h3>
                        <UFormGroup label="Event Name" name="name">
                            <UInput v-model="state.name" required placeholder="Interview Campaign Year Quarter" />
                        </UFormGroup>
                        <UButton type="submit" label="Event anlegen" color="green" variant="soft"
                            class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
                    </UForm>
                </div>
            </UModal>
        </UIBaseCard>
    </Layout>
</template>

<script setup lang="ts">

import { object, string, type InferType } from "yup";
import { computed } from 'vue';

const reversedEvents = computed(() => {
    return [...events.value.items].reverse();
});

const userStore = useUserStore()
const tokenStore = useTokenStore()
const route = useRoute()
const router = useRouter()

const showModal = ref(false)
const state = reactive({ name: "" });

const schema = object({
    name: string().required("Required"),
});

const { data: events, refresh } = await useFetch(`http://localhost:8888/study/${route.params.study_id}/event`, {
    method: "GET",
    headers: { 'Authorization': "Bearer " + tokenStore.access_token },
})

function newInterview(item) {
    router.push({ path: "/interview/" + route.params.study_id + '/event/' + item.id })
}

async function createEvent() {
    try {
        await useCreateEvent(state.name.trim(), route.params.study_id);
        showModal.value = false;
        await refresh();
    } catch (error) {
        console.error("Failed to create event: ", error);
    }
}

</script>

<style scoped>
.base-card:hover {
    background-color: #ededed;
    cursor: pointer;
}

.noHover:hover {
    background-color: white;
    cursor: default;
}
</style>
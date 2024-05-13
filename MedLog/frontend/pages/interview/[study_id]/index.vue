<template>
    <Layout>
        <UIBaseCard @click="newInterview(item)" v-for="item in [...events.items].reverse()" style="text-align: center">
            <h3>{{stringDoc(item.name)}}</h3>
        </UIBaseCard>
        <UIBaseCard v-if="userStore.isAdmin" class="noHover">
            <UButton @click="showModal = true" label="Event anlegen" color="green" variant="soft"
                class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
            <UModal v-model="showModal">
                <div class="p-4" style="text-align: center;">
                    <UForm :schema="schema"
                            :state="state"
                            class="space-y-4"
                            @submit="createEvent">
                        <h3>Event anlegen</h3>
                        <UFormGroup label="Display Name" name="display_name">
                            <UInput v-model="state.display_name" required />
                        </UFormGroup>
                        <UFormGroup label="Abkürzing" name="abbreviation">
                            <UInput v-model="state.abbreviation" required />
                        </UFormGroup>
                        <UCheckbox v-model="state.deactivated" name="deactivated" label="Deactivated" />
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


const showModal = ref(false)
const state = reactive({
    display_name: "",
    deactivated: false,
    no_permissions: false,
    id: "",
    abbreviation: ""
});

const schema = object({
    display_name: string().required("Required"),
    abbreviation: string().required("Required"),
});

function createEvent() {
    showModal.value = false
    console.log(state.display_name.trim());
    console.log(state.abbreviation.trim().replace(" ", ""));
    console.log(state.deactivated)
}

const userStore = useUserStore()
const tokenStore = useTokenStore()
const route = useRoute()
const router = useRouter()


const { data: events } = await useFetch(`http://localhost:8888/study/${route.params.study_id}/event`, {
    method: "GET",
    headers: { 'Authorization': "Bearer " + tokenStore.access_token },
})

function newInterview(item){
    router.push({ path: "/interview/" + route.params.study_id + '/event/' +  item.id})
}

const stringDoc = (ugly_name: string): string => {
    let beautiful_name = ugly_name.replaceAll("-"," ")
    const words = beautiful_name.split(" ");
        const capitalizedWords = words.map(word => {
        return word.charAt(0).toUpperCase() + word.slice(1);
    });
        return capitalizedWords.join(" ");
};

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
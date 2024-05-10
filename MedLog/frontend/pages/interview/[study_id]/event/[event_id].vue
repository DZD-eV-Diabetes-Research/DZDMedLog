<template>
    <Layout>
        <UIBaseCard style="text-align: center">
            <UButton 
                @click="createNewInterview"
                label="New Interview"
                color="green"
                variant="soft"
                class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white"/>
                
                <!-- <UModal v-model="showModal">
                    <div style="text-align: center">
                        <UFormGroup label="Patient Name" name="patientName">
                            <UInput v-model="state.patientName" />
                        </UFormGroup>
                        <Search/>
                    </div>
                </UModal> -->
        </UIBaseCard>
    </Layout>
</template>

<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const showModal = ref(false)

const state = reactive({
    patientName: undefined,
});

function createNewInterview() {
    console.log("hier kommt funktionalität");
    
}

// function createNewInterview() {
//     router.push({ path: "/interview/" + route.params.study_id + "/event/" +  route.params.event_id + "/test"})
// }
</script>
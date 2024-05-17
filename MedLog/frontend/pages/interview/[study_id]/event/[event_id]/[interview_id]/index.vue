<template>
    <Layout>
        <UIBaseCard>
        <h1>Hello from the other side</h1>
        {{ route.params }}
        </UIBaseCard>
    </Layout>
</template>

<script setup lang="ts">

const route = useRoute()
const tokenStore = useTokenStore()

const runtimeConfig = useRuntimeConfig()

// const { data: interview, refresh } = await useFetch(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/event/${route.params.event_id}/interview/${route.params.interview_id}`, {
//     method: "GET",
//     headers: { 'Authorization': "Bearer " + tokenStore.access_token },
// })

</script>
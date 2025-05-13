<template>
    <Layout>
        <UIBaseCard>
           <h1 class="text-4xl">Sie werden zum Start weitergeleitet</h1>
        </UIBaseCard>
    </Layout>
</template>

<script setup lang="ts">

const route = useRoute()
const runtimeConfig = useRuntimeConfig();
const tokenStore = useTokenStore();

const {data:response} = await useFetch(`${runtimeConfig.public.baseURL.slice(0, -5)}${tokenStore.oidcTokenURL}?code=${route.query.code}&state=${route.query.state}`)

tokenStore.loginViaOpenIDToken(response)

</script>
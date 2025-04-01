<template>
    <Layout>
        <UIBaseCard>
            code : {{ route.query.code }}
            <br>
            state : {{ route.query.state }}
        </UIBaseCard>
        <UIBaseCard>
            {{ response }}
        </UIBaseCard>
    </Layout>
</template>

<script setup lang="ts">

const route = useRoute()
const runtimeConfig = useRuntimeConfig();

const {data:response} = await useFetch(`${runtimeConfig.public.baseURL}auth/oidc/token/mockup-server-oidc?code=${route.query.code}&state=${route.query.state}`)

</script>
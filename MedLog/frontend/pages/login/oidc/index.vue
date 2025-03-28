import { UIBaseCard } from '../../../.nuxt/components';
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

<script setup>

const route = useRoute()
const runtimeConfig = useRuntimeConfig();

const {data:response} = await useFetch(`${runtimeConfig.public.baseURL}auth/oidc/token/openid-connect?code=${route.query.code}&state=${route.query.state}`)


</script>
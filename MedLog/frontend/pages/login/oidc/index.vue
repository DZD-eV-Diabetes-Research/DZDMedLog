import { UIBaseCard } from '../../../.nuxt/components';
<template>
    <Layout>
        <UIBaseCard>
            code : {{ route.query.code }}
            <br>
            state : {{ route.query.state }}
        </UIBaseCard>
    </Layout>
</template>

<script setup>

const route = useRoute()

</script>
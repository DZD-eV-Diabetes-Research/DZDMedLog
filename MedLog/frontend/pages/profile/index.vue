<template>
    <Layout>
        <UIBaseCard>
            <div style="text-align:center">
            <h3>Hi {{userStore.userName}}</h3>
            <p>{{userStore.roles}}</p>
            <p>{{userStore.email}}</p>
            <p>{{userStore.displayName}}</p>
            </div>
        </UIBaseCard>
    </Layout>
</template>

<script setup lang="ts">

const userStore = useUserStore();

</script>
<template>
  <Layout>
    <UIBaseCard v-for="event in events.items" :key="event.id">
      <p>{{ event.name }}</p>
    </UIBaseCard>
  </Layout>
</template>

<script setup lang="ts">

const route = useRoute()
const runtimeConfig = useRuntimeConfig()
const tokenStore = useTokenStore()

const { data: events, refresh } = await useFetch(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/event`, {
    method: "GET",
    headers: { 'Authorization': "Bearer " + tokenStore.access_token },
})

</script>
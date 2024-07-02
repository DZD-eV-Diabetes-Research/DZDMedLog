<template>
  <Layout>
    <UIBaseCard>
      <UButton @click="getCompletedEvents(detail)" label="Medikamente übernehmen" color="blue" variant="soft"
        style="margin-left: 10px;"
        class="border border-blue-500 hover:bg-blue-300 hover:border-white hover:text-white" />
    </UIBaseCard>
    <div class="oldDrugs">
      {{ selectedCompleteEvent }}
      <USelectMenu v-model="selectedCompleteEvent" :options="completedItems" />
    </div>
    event: {{ detail.items[0].event.name }}
    <br>
    interview_id: {{ detail.items[0].interview_id }}
    <br>
    {{ completedItems }}
  </Layout>
</template>

<script setup lang="ts">
const tokenStore = useTokenStore()
const route = useRoute()
const runtimeConfig = useRuntimeConfig()

const selectedCompleteEvent = ref()
const completedItems = ref([]);

const { data: events } = await useFetch(`${runtimeConfig.public.baseURL}study/b6f2c61b-d388-4412-8c9a-461ece251116/proband/1234/event`, {
  method: "GET",
  headers: { 'Authorization': "Bearer " + tokenStore.access_token },
})

const { data: detail } = await useFetch(`${runtimeConfig.public.baseURL}study/b6f2c61b-d388-4412-8c9a-461ece251116/proband/1234/intake/details`, {
  method: "GET",
  headers: { 'Authorization': "Bearer " + tokenStore.access_token },
})



async function getCompletedEvents(detail) {
  completedItems.value = detail
  // completedItems.value = completedItems.value.map(event => ({
  //     id: event.id,
  //     event: event,
  //     label: event.name
  //   })) 
  //   selectedCompleteEvent.value = completedItems.value[0]
}

</script>

<style scoped>

.oldDrugs{
  border: 2px;
  border-style: solid;
  border-color: #3a82f6;
}

</style>
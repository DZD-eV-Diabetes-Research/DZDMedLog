<template>
  <Layout>
    {{ test.data }}
    <br>
    <br>
    user: {{ user }}
    <br>
    <br>
    {{ tokenStore }}
  </Layout>
</template>

<script setup lang="ts">
import { useMedlogapi } from '#imports';
const tokenStore = useTokenStore()

const test = await useMedlogapi("/api/health")
const user = await useMedlogapi("/api/user/me")
const user = await useMedlogapi("/")

const test3 = async () => {
  const {$medlogapi} = useNuxtApp();

  const data = await $medlogapi("/api/user/me")
  const test = await $medlogapi("/")
  console.log(data)
}
test3()
</script>

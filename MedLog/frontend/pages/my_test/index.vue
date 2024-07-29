<template>
  <Layout>
    <br>
    <UInput v-model="value" label="eng"/>
    <button @click="test(value, null)">eng</button>
    <button @click="test(null, value)">de</button>
    {{result}}
</Layout>
</template>

<script setup lang="ts">

  const value = ref('')
  const result = ref()

  async function test(eng=null, de=null) {
    if (eng !== null){
    result.value = useDrugSourceTranslator(value.value, null)
    } else 
    {
      result.value = useDrugSourceTranslator(null, value.value)
    }
  }
</script>

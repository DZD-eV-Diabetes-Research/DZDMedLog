<template>
  <Layout>
    <button @click="printDate">get date</button>
  </Layout>
</template>

<script setup lang="ts"> 

async function printDate() {
  let today = new Date().toISOString().slice(0, 10)
  console.log(today);
}

</script>
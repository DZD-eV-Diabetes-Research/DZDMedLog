<template>
     <Layout>
       <p style="text-align: center;"> hi from the other side
      {{ route.params }}</p>
</Layout>
</template>

<script setup lang="ts">

const route = useRoute()

</script>
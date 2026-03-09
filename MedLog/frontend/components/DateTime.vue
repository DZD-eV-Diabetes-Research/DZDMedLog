<script setup lang="ts">
import { useDayjs } from "#dayjs";
import localizedFormat from "dayjs/plugin/localizedFormat";

const dayjs = useDayjs();

dayjs.extend(localizedFormat);

defineProps<{
  datetime: string
}>();
</script>

<template>
  <time :datetime="$dayjs.utc(datetime).format()">
    {{ $dayjs.utc(datetime).local().format('LLL') }}
  </time>
</template>

<style scoped>

</style>

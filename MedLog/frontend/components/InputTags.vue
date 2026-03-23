<script setup lang="ts">
const model = defineModel<string[]>({ required: true });

const inputValue = ref('');

function addValue() {
  const newValues = inputValue.value
    .split(',')
    .map(w => w.trim())
    .filter(w => w !== "");

  model.value.push(...newValues);
  inputValue.value = '';
}

function removeValue(index: number) {
  model.value.splice(index, 1);
}
</script>

<template>
  <UInput
    v-model="inputValue"
    placeholder="Wert eingeben und mit Enter übernehmen"
    @keydown.enter.prevent="addValue()"
    @blur="addValue()"
  />
  <UBadge
    v-for="(word, index) in model"
    :key="index"
    variant="subtle"
    class="mr-2 mt-1"
    :label="word"
  >
    <template #trailing>
      <UIcon
        name="i-heroicons-x-circle-solid"
        title="Wert entfernen"
        class="w-4 h-4 cursor-pointer"
        @click="removeValue(index)"
      />
    </template>
  </UBadge>
</template>

<style scoped>

</style>

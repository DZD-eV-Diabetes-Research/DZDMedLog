<template>
  <Layout>
  <div class="row">
    <div class="col-6">
      <h3>Draggable {{ draggingInfo }}</h3>

      <Draggable
        :list="events.items"
        :disabled="!enabled"
        item-key="name"
        class="list-group"
        ghost-class="ghost"
        @start="dragging = true"
        @end="dragging = false"
      >
        <template #item="{ element }">
          <div class="list-group-item" :class="{ 'not-draggable': !enabled }">
            {{ element.name }}
          </div>
        </template>
      </Draggable>
    </div>
  </div>
  <UButton @click="enabled = !enabled">test</UButton>
</Layout>
</template>

<script setup>
import { ref } from 'vue';
const tokenStore = useTokenStore()


const { data: events } = await useFetch(`http://localhost:8888/study/b6f2c61b-d388-4412-8c9a-461ece251116/event`, {
  method: "GET",
  headers: { 'Authorization': "Bearer " + tokenStore.access_token },
})

let id = 1;
const enabled = ref(true);
const dragging = ref(false);

// function checkMove(e) {
//   console.log(`Future index: ${e.draggedContext.futureIndex}`);
// }

const draggingInfo = computed(() => {
  return dragging.value ? 'under drag' : '';
});
</script>

<style scoped>
.UButtons {
  margin-top: 35px;
}

.ghost {
  opacity: 0.5;
  background: #c8ebfb;
}

.not-draggable {
  cursor: no-drop;
}
</style>
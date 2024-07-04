<template>
  <Layout>
  <div class="row">
    <div class="col-2">
      <div class="form-group">
        <div
          class="btn-group-vertical buttons"
          role="group"
          aria-label="Basic example"
        >
          <button class="btn btn-secondary" @click="add">Add</button>
          <button class="btn btn-secondary" @click="replace">Replace</button>
        </div>

        <div class="form-check">
          <input
            id="disabled"
            type="checkbox"
            v-model="enabled"
            class="form-check-input"
          />
          <label class="form-check-label" for="disabled">DnD enabled</label>
        </div>
      </div>
    </div>

    <div class="col-6">
      <h3>Draggable {{ draggingInfo }}</h3>

      <Draggable
        :list="list"
        :disabled="!enabled"
        item-key="name"
        class="list-group"
        ghost-class="ghost"
        :move="checkMove"
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

    <rawDisplayer class="col-3" :value="list" title="List" />
  </div>
</Layout>
</template>

<script setup>
import { ref } from 'vue';

let id = 1;
const enabled = ref(true);
const list = ref([
  { name: 'John', id: 0 },
  { name: 'Joao', id: 1 },
  { name: 'Jean', id: 2 }
]);
const dragging = ref(false);

function add() {
  list.value.push({ name: `Juan ${id}`, id: id++ });
}

function replace() {
  list.value = [{ name: 'Edgard', id: id++ }];
}

function checkMove(e) {
  console.log(`Future index: ${e.draggedContext.futureIndex}`);
}

const draggingInfo = computed(() => {
  return dragging.value ? 'under drag' : '';
});
</script>

<style scoped>
.buttons {
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

<!-- <template>
  test
</template> -->
<script setup lang="ts">

/**
 * Source: https://vuejs.org/examples/#modal
 */

import { defineProps } from 'vue';

interface Props {
  show: boolean,
  title: string,
  titleColor: string,
}

const props = withDefaults(defineProps<Props>(), {
  show: false,
  title: "string",
  titleColor: '#42b983'
})


</script>

<template>
  <Transition name="modal">
    <div v-if="show" class="modal-mask">
      <div class="modal-container">
        <div class="modal-header">
          <button class="modal-default-button" @click="$emit('close')"><img src="/icons/close.svg"
              class="modal-default-button-image"></button>
          <slot name="header">
            <h3 :style="{ color: titleColor }">{{ title }}</h3>
          </slot>
        </div>

        <div class="modal-body">
          <slot name="body"></slot>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style>
.modal-mask {
  position: fixed;
  z-index: 9998;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  transition: opacity 0.3s ease;
}

.modal-container {
  width: 50%;
  margin: auto;
  padding: 20px 30px;
  background-color: #fff;
  border-radius: 2px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.33);
  transition: all 0.3s ease;
}

.modal-header h3 {
  margin-top: 0;
  color: #42b983;
}

.modal-body {
  margin: 20px 0;
}

.modal-body input {
  border: 2px solid black;
  border-radius: 5px;
}

.modal-default-button {
  float: right;
  padding: 0.5em 0.8em;
}

.modal-default-button-image {
  width: 14px;
}

/*
 * The following styles are auto-applied to elements with
 * transition="modal" when their visibility is toggled
 * by Vue.js.
 *
 * You can easily play with the modal transition by editing
 * these styles.
 */

.modal-enter-from {
  opacity: 0;
}

.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  -webkit-transform: scale(1.1);
  transform: scale(1.1);
}
</style>
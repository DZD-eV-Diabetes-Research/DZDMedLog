import { createApp } from 'vue'
import {createPinia} from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

import router from './router.js';
import App from './App.vue'
import axios from 'axios';
import './interceptor.js'

import BaseCard from './components/UI/BaseCard.vue';
import Modal from './components/UI/Modal.vue'

axios.defaults.baseURL = "http://localhost:8888"

const app = createApp(App)
const pinia = createPinia()

pinia.use(piniaPluginPersistedstate)

app.use(pinia)
app.use(router)

app.component('base-card', BaseCard)
app.component('modal-vue', Modal)


app.mount('#app')

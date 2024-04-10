import { createApp } from 'vue'
import {createPinia} from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

import App from '@/App.vue'
import router from '@/router.ts'
import '@/style.css'

import Vueform from '@vueform/vueform'
import vueformConfig from './../vueform.config'

import BaseCard from '@/components/UI/BaseCard.vue';
import Modal from '@/components/UI/Modal.vue' 

import axios from 'axios';
import '@/interceptor.ts';

axios.defaults.baseURL = "http://localhost:8888"

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
pinia.use(piniaPluginPersistedstate)
app.use(router)

app.use(Vueform, vueformConfig)

app.component('base-card', BaseCard)
app.component('modal-vue', Modal)

app.mount('#app')

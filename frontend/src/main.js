import { createApp } from 'vue'
import router from './router.js';
import store from './store/index.js'
import App from './App.vue'

import BaseCard from './components/UI/BaseCard.vue';

const app = createApp(App)

app.use(router)
app.use(store)

app.component('base-card', BaseCard)

app.mount('#app')

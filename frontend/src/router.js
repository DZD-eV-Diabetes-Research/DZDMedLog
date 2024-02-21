import { createRouter, createWebHistory } from 'vue-router';
import store from './store/index.js'

import Login from "./components/Auth/Login.vue"
import UserView from "./components/UI/UserView.vue"
import NotFound from "./components/UI/NotFound.vue"

const router = createRouter({
    history: createWebHistory(),
    routes: [
        { path: '/', redirect: "/auth" },
        { path: '/auth', component: Login },
        { path: '/user', component: UserView, beforeEnter:(to, from, next) => {
            if(store.getters.access_token){
                next()
            } else {
                next("/")
            }
        }
    
    
    },
        { path: '/:notFound(.*)', component: NotFound }
    ]
});

export default router
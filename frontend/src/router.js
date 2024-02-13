import { createRouter, createWebHistory } from 'vue-router';

import Login from "./components/Auth/Login.vue"
import NotFound from "./components/UI/NotFound.vue"

const router = createRouter({
    history: createWebHistory(),
    routes: [
        { path: '/', redirect: "/auth" },
        { path: '/auth', component: Login },
        { path: '/:notFound(.*)', component: NotFound }
    ]
});

export default router
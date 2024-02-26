//import { useTokenStore } from '@/stores/TokenStore'
import { createRouter, createWebHistory } from 'vue-router';
import { useTokenStore } from '@/stores/TokenStore'

import Login from "./components/Auth/Login.vue"
import UserView from "./components/UI/UserView.vue"
import NotFound from "./components/UI/NotFound.vue"

const router = createRouter({
    history: createWebHistory(),
    routes: [
        { path: '/', redirect: "/auth" },
        {
            path: '/auth',
            component: Login,
            meta: { requiresAuth: false }, 
            beforeEnter: (to, from, next) => {
                const tokenStore = useTokenStore()
                const refreshToken = tokenStore.get_refresh_token; 

                if (refreshToken) {
                    next("/user");
                } else {
                    next();
                }
            }
        },
        {
            path: '/user',
            component: UserView,
            meta: { requiresAuth: true }, 
            beforeEnter: (to, from, next) => {
                const tokenStore = useTokenStore()
                const refreshToken = tokenStore.get_refresh_token; 
                if (refreshToken) {
                    next();
                } else {
                    next("/auth");
                }
            }
        },
        { path: '/:notFound(.*)', component: NotFound }
    ]
});

router.beforeEach((to, from, next) => {
    const tokenStore = useTokenStore();
    const refreshToken = tokenStore.get_refresh_token;
    const isLoggedIn = tokenStore.get_logged_status;

    if (to.meta.requiresAuth && (!refreshToken || !isLoggedIn)) {
        console.log(to.meta.requiresAuth && !refreshToken)
        next('/auth');
    } else {
        next();
    }
});

// router.beforeEach((to, from, next) => {
//     const tokenStore = useTokenStore();
//     const isLoggedIn = tokenStore.get_logged_status;

//     if (!isLoggedIn) {
//         next('/auth');
//     } else {
//         next();
//     }
// });

export default router;

import { createRouter, createWebHistory } from 'vue-router';
import { useTokenStore } from '@/stores/TokenStore'

import Login from "./components/Auth/Login.vue"
import UserView from "./components/UI/User/UserView.vue"

const routes = [
    { path: '/', redirect: "/auth" },
    {
        path: '/auth',
        name: 'authentication',
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
        name: 'user',
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
    {
        path: '/profile',
        name: 'profile',
        component: ()=>import('./components/UI/User/UserProfile.vue'),
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
    {
        path: '/studies',
        name: 'studies',
        component: ()=>import('./components/UI/Studies/UserStudies.vue'),
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
    {
        path: '/studies/:study',
        name: 'study',
        component: ()=>import('./components/UI/Studies/MyStudy.vue'),
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
    {
        path: '/construction',
        name: 'construction',
        component: ()=>import('./components/UI/PageConstruction.vue'),
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
    { path: '/:notFound(.*)', name:'notfound', component: ()=>import('./components/UI/NotFound.vue') }
]

const router = createRouter({
    history: createWebHistory(),
    routes
});

router.beforeEach((to, from, next) => {
    const tokenStore = useTokenStore();
    const refreshToken = tokenStore.get_refresh_token;

    if (to.meta.requiresAuth && !refreshToken) {
        next('/auth');
    } else {
        next();
    }
});

export default router;

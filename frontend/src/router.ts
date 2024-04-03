import { createRouter, createWebHistory, RouteLocationNormalized, NavigationGuardNext } from 'vue-router';
import { useTokenStore } from '@/stores/TokenStore'

import Login from "@/components/Authentication/Login.vue"
import UserView from "@/components/UI/User/UserView.vue"

const routes = [
    { path: '/', redirect: "/auth" },
    {
        path: '/auth',
        name: 'authentication',
        component: Login,
        meta: { requiresAuth: false }, 
        beforeEnter: (to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) => {
            const tokenStore = useTokenStore()
            const refreshToken = tokenStore.refreshToken; 

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
        beforeEnter: (to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) => {
            const tokenStore = useTokenStore()
            const refreshToken = tokenStore.refreshToken; 
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
        component: ()=>import('@/components/UI/User/UserProfile.vue'),
        meta: { requiresAuth: true }, 
        beforeEnter: (to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) => {
            const tokenStore = useTokenStore()
            const refreshToken = tokenStore.refreshToken; 
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
        component: ()=>import('@/components/UI/Studies/UserStudies.vue'),
        meta: { requiresAuth: true }, 
        beforeEnter: (to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) => {
            const tokenStore = useTokenStore()
            const refreshToken = tokenStore.refreshToken

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
        beforeEnter: (to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) => {
            const tokenStore = useTokenStore()
            const refreshToken = tokenStore.refreshToken; 

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
        component: ()=>import('@/components/UI/PageConstruction.vue'),
        meta: { requiresAuth: true }, 
        beforeEnter: (to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) => {
            console.log(to, from);
            const tokenStore = useTokenStore()
            const refreshToken = tokenStore.refreshToken; 

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

router.beforeEach((to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) => {
    const tokenStore = useTokenStore();
    const refreshToken = tokenStore.refreshToken;

    if (to.meta.requiresAuth && !refreshToken) {
        next('/auth');
    } else {
        next();
    }
});

export default router;

import {navigateTo} from "#imports";

export default defineNuxtPlugin((nuxtApp) => {
    nuxtApp.hook('openFetch:onResponseError:medlogapi', async (ctx) => {
        if (ctx.response.status === 401 && ctx.request !== '/api/auth/logout') {
            await navigateTo('/login')
        }
    })
})

export default defineNuxtPlugin((nuxtApp) => {
    const runTimeConfig = useRuntimeConfig();
    const tokenStore = useTokenStore();



    const api = $fetch.create({
        baseURL: `${runTimeConfig.public.baseURL}`,
        onRequest({ request, options, error }) {
            if (tokenStore?.access_token) {
                options.headers.set('Authorization', `Bearer ${tokenStore?.access_token}`)
            }
        },
        async onResponseError({ response }) {
            if (response.status === 401) {
                console.log("❌ Token abgelaufen");
                tokenStore.loggedIn = false
                tokenStore.expiredToken = true
                await nuxtApp.runWithContext(() => navigateTo('/'))
            }
        }
    })

    // Expose to useNuxtApp().$api
    return {
        provide: {
            api
        }
    }
})

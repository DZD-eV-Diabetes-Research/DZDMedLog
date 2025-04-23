export default defineNuxtPlugin((nuxtApp) => {
    const { session } = useUserSession()
    const runTimeConfig = useRuntimeConfig();


    const api = $fetch.create({
        baseURL: `${runTimeConfig.public.baseURL}`,
        onRequest({ request, options, error }) {
            if (session.value?.token) {
                options.headers.set('Authorization', `Bearer ${session.value?.token}`)
            }
        },
        async onResponseError({ response }) {
            if (response.status === 401) {
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

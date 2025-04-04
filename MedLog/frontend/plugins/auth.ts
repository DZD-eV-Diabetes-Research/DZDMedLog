export default defineNuxtPlugin((nuxtApp) => {
    const tokenStore = useTokenStore()

    nuxtApp.hook('fetch:response', async (context) => {
        if (context.response.status === 401) {
            const responseData = await context.response.json()
            if (responseData.message.includes('Signature has expired')) {
                tokenStore.expiredToken = true
                tokenStore.loggedIn = false
                return navigateTo('/')
            }
        }
    })
})

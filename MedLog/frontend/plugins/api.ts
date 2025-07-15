// plugins/api.ts
export default defineNuxtPlugin({
    enforce: 'pre',
    setup() {
        const config = useRuntimeConfig()
        const clients = config.public.openFetch
        const router = useRouter()

        if (!clients) return { provide: {} }

        const handleUnauthorized = () => {
            // const current = router.currentRoute.value
            // if (current.fullPath !== '/login' && !current.query.redirect) {
            //     router.push({ path: '/login', query: { redirect: current.fullPath } })
            // }
            console.log("handle unauth");
        }

        return {
            provide: Object.entries(clients).reduce((acc, [name, options]) => ({
                ...acc,
                [name]: createOpenFetch(localOptions => ({
                    ...options,
                    ...localOptions,
                    onRequest(ctx) {
                        // Beispiel: Auth header
                        const tokenStore = useTokenStore()
                        if (tokenStore.access_token) {
                            ctx.options.headers = {
                                ...ctx.options.headers,
                                Authorization: `Bearer ${tokenStore.access_token}`,
                            }
                        }

                        if (typeof localOptions?.onRequest === 'function') {
                            localOptions.onRequest(ctx)
                        }
                    },
                    onResponse(ctx) {
                        if (ctx.response?.status === 401) handleUnauthorized()
                        localOptions?.onResponse?.(ctx)
                    },
                    onResponseError(ctx) {
                        if (ctx.response?.status === 401) handleUnauthorized()
                        localOptions?.onResponseError?.(ctx)
                    }
                }))
            }), {})
        }
    }
})
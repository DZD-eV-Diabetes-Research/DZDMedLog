// plugins/api.ts
export default defineNuxtPlugin({
    enforce: 'pre',
    setup() {
        const config = useRuntimeConfig()
        const clients = config.public.openFetch
        const router = useRouter()

        if (!clients) return { provide: {} }

        const handleUnauthorized = () => {
            const current = router.currentRoute.value
            if (current.fullPath !== '/login' && !current.query.redirect) {
                router.push({ path: '/login', query: { redirect: current.fullPath } })
            }
            console.log("handle unauth");
        }

        return {
            provide: Object.entries(clients).reduce((acc, [name, options]) => ({
                ...acc,
                [name]: createOpenFetch(localOptions => ({
                    ...options,
                    ...localOptions,
                    onRequest: localOptions?.onRequest,
                    onResponse(ctx) {
                        if (ctx.response?.status === 401) handleUnauthorized()
                            ; (localOptions?.onResponse as any)?.(ctx)
                    },
                    onResponseError(ctx) {
                        if (ctx.response?.status === 401) handleUnauthorized()
                            ; (localOptions?.onResponseError as any)?.(ctx)
                    }
                }))
            }), {})
        }
    }
})
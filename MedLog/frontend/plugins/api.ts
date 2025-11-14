// plugins/api.ts
export default defineNuxtPlugin({
    enforce: 'pre',
    setup() {
        const config = useRuntimeConfig()
        const clients = config.public.openFetch
        const router = useRouter()

        if (!clients) return { provide: {} }

        const handleUnauthorized = async () => {
            const current = router.currentRoute.value
            if (current.fullPath !== '/login' && !current.query.redirect) {
                await router.push({ path: '/login', query: { target_path: current.fullPath } })
            }
            console.log("handle unauth");
        }

        return {
            provide: Object.entries(clients).reduce((acc, [name, options]) => ({
                ...acc,
                [name]: createOpenFetch(localOptions => {
                    return {
                        ...options,
                        ...localOptions,
                        onRequest: localOptions?.onRequest,
                        async onResponse(ctx) {
                            if (ctx.response?.status === 401) {
                                await handleUnauthorized()
                            }
                            (localOptions?.onResponse as any)?.(ctx)
                        },
                        async onResponseError(ctx) {
                            if (ctx.response?.status === 401) {
                                await handleUnauthorized()
                            }
                            (localOptions?.onResponseError as any)?.(ctx)
                        }
                    };
                })
            }), {})
        }
    }
})

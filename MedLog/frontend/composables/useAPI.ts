// A wrapper around useFetch function that uses the plugins/api.ts code

import type { UseFetchOptions } from 'nuxt/app'

export function useAPI<T>(
    url: string | (() => string),
    options?: UseFetchOptions<T>,
) {
    return useFetch(url, {
        ...options,
        $fetch: useNuxtApp().$api as typeof $fetch
    })
}
import { setup } from '@nuxt/test-utils'

await setup({
    server: true,
    nuxtConfig: {
        server: {
            port: 3000
        }
    }
})
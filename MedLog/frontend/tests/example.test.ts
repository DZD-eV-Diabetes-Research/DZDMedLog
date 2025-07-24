import { expect, test } from '@nuxt/test-utils/playwright'

test('test', async ({ page, goto }) => {
    await goto('/login', { waitUntil: 'hydration' })
    
    await expect(page.getByRole('heading', { name: 'Der Backendstatus ist' }))
})

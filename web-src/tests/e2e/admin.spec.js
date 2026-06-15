import {expect, test} from '@playwright/test'

// Admin app boot: second Vue application (own router + store). Covers the
// admin mount path verified manually after the Vue 3 migration.

test.describe('Admin app', () => {

    test('loads with Logs/Scripts tabs and defaults to logs', async ({page}) => {
        await page.goto('/admin.html')

        await expect(page.locator('.admin-page')).toBeVisible()
        await expect(page).toHaveURL(/#\/logs$/)
        await expect(page.locator('.v-tab', {hasText: 'Logs'})).toBeVisible()
        await expect(page.locator('.v-tab', {hasText: 'Scripts'})).toBeVisible()
    })

    test('scripts tab lists configured scripts with an Add button', async ({page}) => {
        await page.goto('/admin.html#/scripts')

        await expect(page.locator('.add-script-btn')).toBeVisible()
        await expect(page.locator('.v-list-item', {hasText: 'E2E Echo'})).toBeVisible()
    })
})

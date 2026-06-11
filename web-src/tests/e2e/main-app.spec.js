import {expect, test} from '@playwright/test'

// Critical path: main page boot, script selection through a group, and
// parameter rendering. Each assertion maps to a real regression found during
// the Vue 3 migration (router.currentRoute.value, group expansion, parameter
// panel rendering).

test.describe('Main app', () => {

    test('loads and shows the scripts sidebar', async ({page}) => {
        await page.goto('/index.html')

        await expect(page).toHaveTitle('Script server')
        await expect(page.locator('.scripts-list')).toBeVisible()
        await expect(page.locator('.script-group', {hasText: 'E2E Group'})).toBeVisible()
    })

    test('expands a group and selects a script -> parameters render', async ({page}) => {
        await page.goto('/index.html')

        await page.locator('.script-group', {hasText: 'E2E Group'}).click()

        const scriptLink = page.locator('.script-list-item', {hasText: 'E2E Echo'})
        await expect(scriptLink).toBeVisible()
        await scriptLink.click()

        // parameter panel renders the three fixture parameters
        const params = page.locator('.script-parameters-panel .parameter')
        await expect(params).toHaveCount(3)
        await expect(page.locator('.script-parameters-panel')).toContainText('Mode')
        await expect(page.locator('.script-parameters-panel')).toContainText('Message')
        await expect(page.locator('.script-parameters-panel')).toContainText('ConfFile')

        // execute button present
        await expect(page.locator('.button-execute')).toBeVisible()
    })

    test('deep link to a script renders its parameters (router regression)', async ({page}) => {
        // Direct hash navigation: this is the exact scenario broken by the
        // Vue Router 4 `currentRoute.value` regression.
        await page.goto('/index.html#/' + encodeURIComponent('E2E Echo'))

        const params = page.locator('.script-parameters-panel .parameter')
        await expect(params).toHaveCount(3)
        await expect(page.locator('.script-parameters-panel')).toContainText('Message')
    })
})

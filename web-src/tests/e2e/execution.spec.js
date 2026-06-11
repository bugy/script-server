import {expect, test} from '@playwright/test'

// Full execution path in a real browser: XSRF token mode (the _xsrf cookie
// must be readable by JS and echoed as X-XSRFToken — regression of the
// HttpOnly bug), POST /executions/start, websocket streaming, and the
// log panel rendering (regression of the logChunks deep-watch bug).

async function openEchoScript(page) {
    await page.goto('/index.html#/' + encodeURIComponent('E2E Echo'))
    await expect(page.locator('.script-parameters-panel .parameter')).toHaveCount(2)
}

function paramInput(page, label) {
    return page.locator('.script-parameters-panel .parameter')
        .filter({has: page.locator('label', {hasText: label})})
        .locator('input')
}

test.describe('Script execution', () => {

    // NOTE: order matters. Finished executions stay attached server-side
    // (/executions/active) for the rest of the suite, so a later page load on
    // the same script re-binds the previous execution and its log panel. The
    // validation test must therefore run BEFORE any successful execution.

    test('execute without required parameter is blocked', async ({page}) => {
        await openEchoScript(page)

        // Message is required and empty: clicking Execute must show the
        // validation panel and must NOT start an execution.
        await page.locator('.button-execute').click()

        const validationPanel = page.locator('.validation-panel')
        await expect(validationPanel).toBeVisible()
        await expect(validationPanel).toContainText('Message')

        await expect(page.locator('.log-panel .log-content')).toBeHidden()
    })

    test('executes a script and streams its output to the log panel', async ({page}) => {
        await openEchoScript(page)

        await paramInput(page, 'Message').fill('hello-e2e')

        await page.locator('.button-execute').click()

        const log = page.locator('.log-panel .log-content')
        await expect(log).toContainText('e2e: started', {timeout: 15_000})
        await expect(log).toContainText('--mode alpha --message hello-e2e')
        await expect(log).toContainText('e2e: done', {timeout: 15_000})
    })

    test('changes a combobox value before executing', async ({page}) => {
        // Exercises the Vuetify v-select dropdown in a real browser.
        await openEchoScript(page)

        const modeParam = page.locator('.script-parameters-panel .parameter')
            .filter({has: page.locator('label', {hasText: 'Mode'})})
        await modeParam.locator('.v-field').click()

        await page.locator('.v-overlay .v-list-item', {hasText: 'beta'}).click()

        await paramInput(page, 'Message').fill('combo-test')
        await page.locator('.button-execute').click()

        const log = page.locator('.log-panel .log-content')
        await expect(log).toContainText('--mode beta --message combo-test', {timeout: 15_000})
    })
})

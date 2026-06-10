import {defineConfig, devices} from '@playwright/test'

// E2E suite against the real Python backend serving the production build
// (web/). The backend is started automatically with an isolated config
// (tests/e2e/fixtures/conf — never the developer's real conf/), on port 5099.
//
// Run with: npm run test:e2e  (builds the frontend first)
export default defineConfig({
    testDir: './tests/e2e',
    testMatch: '**/*.spec.js',
    fullyParallel: false,
    workers: 1,
    retries: process.env.CI ? 2 : 0,
    reporter: process.env.CI ? [['github'], ['html', {open: 'never'}]] : 'list',

    use: {
        baseURL: 'http://localhost:5099',
        trace: 'on-first-retry',
        screenshot: 'only-on-failure'
    },

    projects: [
        {name: 'chromium', use: {...devices['Desktop Chrome']}}
    ],

    webServer: {
        command: 'bash tests/e2e/server.sh',
        url: 'http://localhost:5099/index.html',
        reuseExistingServer: !process.env.CI,
        timeout: 120_000
    }
})

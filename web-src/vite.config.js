import {defineConfig} from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import {fileURLToPath, URL} from 'node:url'

export default defineConfig({
    plugins: [vue()],

    // Relative public path (assets referenced as ./...), so the build can be
    // served from any sub-path.
    base: '',

    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url))
        },
        // Allow imports without explicit .vue extension (matches webpack behaviour)
        extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json', '.vue']
    },

    build: {
        outDir: '../web',
        emptyOutDir: true,
        rollupOptions: {
            input: {
                index: fileURLToPath(new URL('./index.html', import.meta.url)),
                admin: fileURLToPath(new URL('./admin.html', import.meta.url)),
                login: fileURLToPath(new URL('./login.html', import.meta.url))
            }
        }
    },

    server: {
        proxy: {
            // Forward API + WebSocket traffic to the running Python dev server.
            // Adjust or extend these paths if additional routes are needed.
            '/api': {target: 'http://localhost:5000', changeOrigin: true},
            '/executions': {target: 'http://localhost:5000', changeOrigin: true, ws: true},
            '/scripts': {target: 'http://localhost:5000', changeOrigin: true},
            '/admin/scripts': {target: 'http://localhost:5000', changeOrigin: true},
            '/logout': {target: 'http://localhost:5000', changeOrigin: true},
            '/theme': {target: 'http://localhost:5000', changeOrigin: true}
        }
    },

    // ── Vitest ────────────────────────────────────────────────────────────────
    test: {
        environment: 'jsdom',
        globals: true,
        setupFiles: ['./tests/unit/setup.js'],
        include: ['tests/unit/**/*_test.js'],
        server: {
            deps: {
                // vuetify: its library code imports .css files directly, which
                // Node's ESM loader can't handle — inlining routes them through
                // Vite's pipeline instead ("Unknown file extension .css" otherwise).
                inline: [/vuetify/]
            }
        }
    }
})

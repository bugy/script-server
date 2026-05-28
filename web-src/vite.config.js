import {defineConfig} from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import {fileURLToPath, URL} from 'node:url'

export default defineConfig({
    plugins: [vue()],

    // Relative public path — equivalent to vue.config.js publicPath: ''
    base: '',

    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url))
        },
        // Allow imports without explicit .vue extension (matches webpack behaviour)
        extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json', '.vue']
    },

    css: {
        preprocessorOptions: {
            scss: {
                // Make project variables and materialize tokens available in every .scss / <style lang="scss">
                // Using loadPaths so node_modules imports resolve without ~prefix
                loadPaths: [
                    fileURLToPath(new URL('./node_modules', import.meta.url))
                ],
                additionalData: [
                    `@import "${fileURLToPath(new URL('./src/assets/css/color_variables.scss', import.meta.url))}";`,
                    '@import "materialize-css/sass/components/_variables.scss";',
                    '@import "materialize-css/sass/components/_global.scss";',
                    '@import "materialize-css/sass/components/_typography.scss";',
                ].join('\n')
            }
        }
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
        include: ['tests/unit/**/*_test.js']
    }
})

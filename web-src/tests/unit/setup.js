/**
 * Vitest global setup — replaces the Karma/Mocha tests/unit/index.js entry.
 *
 * - Extends `expect` with jest-dom and jest-extended matchers
 * - Registers @vue/test-utils auto-unmount after each test
 */
import {expect, afterEach} from 'vitest'
import * as domMatchers from '@testing-library/jest-dom/matchers'
import jestExtended from 'jest-extended'
import {config, enableAutoUnmount} from '@vue/test-utils'
import vueDirectives from '@/common/vueDirectives'
import {forEachKeyValue} from '@/common/utils/common'
import vuetify from '@/common/vuetifyPlugin'

expect.extend(domMatchers)
expect.extend(jestExtended)

// jsdom has no ResizeObserver; some Vuetify components observe element sizes.
if (!globalThis.ResizeObserver) {
    globalThis.ResizeObserver = class {
        observe() {}

        unobserve() {}

        disconnect() {}
    }
}

// jsdom has no VisualViewport; Vuetify's VOverlay connected location strategy
// (used by v-menu/v-combobox dropdowns) subscribes to its resize/scroll events.
if (!globalThis.visualViewport) {
    const viewport = new EventTarget()
    Object.assign(viewport, {
        width: 1280,
        height: 800,
        offsetLeft: 0,
        offsetTop: 0,
        pageLeft: 0,
        pageTop: 0,
        scale: 1
    })
    globalThis.visualViewport = viewport
}

// Vuetify components (migration in progress) need the plugin on every mount.
config.global.plugins = [vuetify]

// jsdom has no layout engine; override offsetParent so code walking the chain
// (e.g. Vuetify's isFixedPosition) doesn't crash under jsdom.
Object.defineProperty(globalThis.HTMLElement.prototype, 'offsetParent', {
    configurable: true,
    get() {
        // Real browsers return null for <body>/<html>; keeping that here is
        // essential — code walking the offsetParent chain (e.g. Vuetify's
        // isFixedPosition) would otherwise bounce between body and html forever.
        if (this === document.body || this === document.documentElement) {
            return null
        }
        return this.parentElement || document.body
    }
})

// jsdom doesn't implement scrollIntoView; stub it so Vuetify components don't throw.
if (!globalThis.Element.prototype.scrollIntoView) {
    globalThis.Element.prototype.scrollIntoView = function () {}
}

// jsdom has no layout engine, so HTMLElement.innerText is not implemented
// (reads return undefined, writes don't create text nodes). Map it to
// textContent — equivalent for the plain-text usages in the app/tests.
Object.defineProperty(globalThis.HTMLElement.prototype, 'innerText', {
    configurable: true,
    get() {
        return this.textContent
    },
    set(value) {
        this.textContent = value
    }
})

// Register the app's custom directives globally for every mounted component.
// Vue 3 / VTU v2 has no `createLocalVue`; directives go through config.global instead.
// This replaces the old `createScriptServerTestVue()` + `localVue` mount option.
forEachKeyValue(vueDirectives, (id, definition) => {
    config.global.directives[id] = definition
})

// Auto-unmount Vue wrappers after every test (Vue 3 equivalent of enableAutoDestroy)
enableAutoUnmount(afterEach)

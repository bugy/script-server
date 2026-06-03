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
// Populate the global materialize `M` (and the `Component` base class) the same
// way the running app does. In the app, importing any materialize piece sets up
// the shared global `M`; components such as TimePicker reference `M.updateTextFields`
// / `M.validate_field` (from materialize forms) without importing it themselves.
// Loading input-fields here pulls in `global` + `forms` so that global exists in tests.
import '@/common/materializecss/imports/input-fields'

expect.extend(domMatchers)
expect.extend(jestExtended)

// jsdom has no layout engine, so HTMLElement.offsetParent is always null. Some
// materialize-css components (e.g. Dropdown positioning) call
// `el.offsetParent.getBoundingClientRect()` and would crash. Provide a sane
// fallback so those components can run under jsdom. (Karma used a real browser.)
// Note: jsdom already defines offsetParent (returning null); override it forcibly.
Object.defineProperty(globalThis.HTMLElement.prototype, 'offsetParent', {
    configurable: true,
    get() {
        return this.parentElement || document.body
    }
})

// jsdom doesn't implement scrollIntoView at all (no layout engine). Several
// components and materialize helpers call it; stub it as a no-op so they don't
// throw under jsdom (an unhandled throw from a timer/interval can fail the run).
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

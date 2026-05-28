/**
 * Vitest global setup — replaces the Karma/Mocha tests/unit/index.js entry.
 *
 * - Extends `expect` with jest-dom and jest-extended matchers
 * - Makes jQuery available as window.$ (required by materialize-css init code)
 * - Registers @vue/test-utils auto-destroy after each test
 */
import {expect, afterEach} from 'vitest'
import * as domMatchers from '@testing-library/jest-dom/matchers'
import jestExtended from 'jest-extended'
import $ from 'jquery'
import {enableAutoUnmount} from '@vue/test-utils'

expect.extend(domMatchers)
expect.extend(jestExtended)

// Make jQuery globally available (materialize-css and some components rely on it)
globalThis.$ = $
globalThis.jQuery = $

// Auto-unmount Vue wrappers after every test (Vue 3 equivalent of enableAutoDestroy)
enableAutoUnmount(afterEach)

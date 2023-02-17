import expect from 'expect';
import extendedMatchers from 'jest-extended/dist/matchers'
import $ from 'jquery';
import {enableAutoDestroy} from '@vue/test-utils'

const domMatches = require('@testing-library/jest-dom/matchers')

expect.extend(domMatches);
expect.extend(extendedMatchers);
window.expect = expect;
window.$ = $;

const context = require.context(
    '.',
    true,
    /_test.js$/
);

context.keys().forEach(context);

enableAutoDestroy(afterEach)

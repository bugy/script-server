import expect from 'expect';
import extendedMatchers from 'jest-extended/dist/matchers'
import $ from 'jquery';

expect.extend(extendedMatchers);
window.expect = expect;
window.$ = $;

const context = require.context(
    '.',
    true,
    /_test.js$/
);

context.keys().forEach(context);

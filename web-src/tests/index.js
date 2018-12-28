const context = require.context(
    '.',
    false,
    /_test.js$/
);

context.keys().forEach(context);
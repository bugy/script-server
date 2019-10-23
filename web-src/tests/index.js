const context = require.context(
    '.',
    true,
    /_test.js$/
);

context.keys().forEach(context);
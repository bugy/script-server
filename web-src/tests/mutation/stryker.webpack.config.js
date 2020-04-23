const path = require('path');

module.exports = {
    entry: {'stryker_entry': './tests/unit/terminal_model_test.js'},
    resolve: {
        alias: {
            '@': path.resolve('src')
        }
    }
};
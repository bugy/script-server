const merge = require('webpack-merge');
const common = require('./webpack.common.js');

module.exports = merge(common, {
    entry: {'test_entry': './tests/terminal_model_test.js'},
    mode: 'development',
    devtool: 'inline-source-map'
});
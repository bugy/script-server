const merge = require('webpack-merge');
const common = require('./webpack.common.js');

module.exports = merge(common, {
    mode: 'production',
    devtool: 'source-map',
    resolve: {
        alias: {
            // TODO this can be removed after migration to .vue
            vue: 'vue/dist/vue.min.js'
        }
    }
});
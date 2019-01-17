const merge = require('webpack-merge');
const common = require('./webpack.common.js');
const path = require('path');
const webpack = require('webpack');

module.exports = merge(common, {
    mode: 'development',
    devtool: 'inline-source-map',
    devServer: {
        contentBase: path.resolve(__dirname + '/../web'),
        hot: true,
        proxy: [{
            context: ['/scripts', '/executions', '/conf', '/auth', '/result_files', '/admin', '/login', '/logout'],
            target: 'http://localhost:5000',
            ws: true
        }]
    },
    plugins: [
        new webpack.HotModuleReplacementPlugin()
    ]
});
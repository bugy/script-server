//TODO fix materializecss styles on index and login forms

const path = require('path');
const webpack = require('webpack');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const CopyWebpackPlugin = require('copy-webpack-plugin');
const devMode = process.env.NODE_ENV !== 'production';

module.exports = {
    entry: {
        'index': './js/index.js',
        'admin/admin': './js/admin/admin.js',
        'login': './js/login.js'
    },
    output: {
        filename: '[name].js',
        path: path.resolve(__dirname + '/../web')
    },
    devServer: {
        contentBase: path.resolve(__dirname + '/../web'),
        hot: true,
        proxy: [{
            context: ['/scripts', '/conf', '/auth', '/result_files', '/admin', '/login', '/logout'],
            target: 'http://localhost:5000',
            ws: true
        }]
    },
    devtool:
        'inline-source-map',
    resolve: {
        alias: {
            vue: 'vue/dist/vue.js'
        }
    },
    plugins:
        [
            new webpack.ProvidePlugin({
                '$': 'jquery',
                jQuery: 'jquery',
                'window.$': 'jquery',
                'window.jQuery': 'jquery',
                'jquery': 'jquery'
            }),
            new HtmlWebpackPlugin({
                template: 'index.html',
                chunks: ['index'],
                filename: 'index.html',
                inject: false
            }),
            new HtmlWebpackPlugin({
                template: 'admin.html',
                chunks: ['admin/admin'],
                filename: 'admin.html',
                inject: false
            }),
            new HtmlWebpackPlugin({
                template: 'login.html',
                chunks: ['login'],
                filename: 'login.html',
                inject: false
            }),
            new CopyWebpackPlugin([
                {from: 'images', to: 'images'},
                {from: 'css', to: 'css'}
            ]),
            new MiniCssExtractPlugin({
                filename: "[name]-deps.css"
            }),
            new webpack.HotModuleReplacementPlugin()
        ],
    module:
        {
            rules: [
                {
                    test: /\.js$/,
                    exclude: /node_modules/,
                    use: {
                        loader: 'babel-loader',
                        options: {
                            presets: ['@babel/preset-env']
                        }
                    }
                },
                {
                    test: /\.css$/,
                    include: /node_modules/,
                    loaders: [
                        MiniCssExtractPlugin.loader,
                        'css-loader']
                },
                {
                    test: /\.(woff(2)?|ttf|eot)$/,
                    include: /node_modules/,
                    use: {
                        loader: 'file-loader',
                        options: {
                            name: '[name].[ext]',
                            outputPath: 'fonts',
                            publicPath: '/fonts',
                            mimetype: 'application/font-woff'
                        }
                    }
                }
            ]
        }
}
;
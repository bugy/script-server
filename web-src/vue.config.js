const webpack = require('webpack');

module.exports = {
    // don't set absolute paths, otherwise reverse proxies with a custom path won't work
    publicPath: '',

    outputDir: '../web',

    devServer: {
        proxy: {
            '': {
                target: 'http://localhost:5000'
            },
            '/': {
                target: 'ws://localhost:5000',
                ws: true,
                headers: {
                    Origin: 'http://localhost:5000'
                }
            }
        }
    },

    pages: {
        index: {
            entry: 'src/main-app/index.js',
            template: 'public/index.html',
            chunks: ['chunk-vendors', 'chunk-common', 'index']
        }
    },

    css: {
        loaderOptions: {
            scss: {
                prependData: '@import "./src/assets/css/color_variables.scss"; '
                    + '@import "materialize-css/sass/components/_variables.scss"; '
                    + '@import "materialize-css/sass/components/_normalize.scss"; '
                    + '@import "materialize-css/sass/components/_global.scss"; '
                    + '@import "materialize-css/sass/components/_typography.scss"; '
            }
        }
    },

    configureWebpack: {
        // webpack removes "class Component" during tree-shaking. Even if it's imported somewhere
        // so we explicitly load it
        plugins: [new webpack.ProvidePlugin({Component: 'exports-loader?Component!materialize-css/js/component.js'})]
    }
};
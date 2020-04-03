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
    }
};
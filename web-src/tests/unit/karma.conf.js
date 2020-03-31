"use strict";

var webpackConfig = require('../webpack.dev.js');

// we need to explicitly override entries to avoid full files compilation
// and empty entries are not allowed
webpackConfig.entry = {'some_entry': './tests/test_utils.js'};
webpackConfig.devtool = 'inline-source-map';
webpackConfig.mode = 'development';
webpackConfig.watch = true;

for (const rule of webpackConfig.module.rules) {
    if (!rule.test) {
        continue;
    }

    if (/\.css/.test(rule.test)) {
        // karma-webpack cannot handle MiniCssExtractPlugin, so just remove it
        for (let i = 0; i < rule.loaders.length; i++) {
            const loader = rule.loaders[i];

            if (/mini-css-extract-plugin/.test(loader)) {
                rule.loaders.splice(i, 1);
                i--;
            }
        }
    } else if (/\.js/.test(rule.test)) {
        const options = rule.use.options;
        if ((typeof options.plugins) === 'undefined') {
            options.plugins = ['babel-plugin-rewire'];
        } else {
            options.plugins.push('babel-plugin-rewire');
        }
    }
}


module.exports = function (config) {
    config.set({

        // base path that will be used to resolve all patterns (eg. files, exclude)
        basePath: '..',


        // frameworks to use
        // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
        frameworks: ['mocha'],


        // list of files / patterns to load in the browser
        files: [
            'tests/index.js',
            'node_modules/materialize-css/dist/css/materialize.css'
        ],


        exclude: [],


        // preprocess matching files before serving them to the browser
        // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
        preprocessors: {
            '**/*.js': ['webpack', 'sourcemap']
        },

        webpack: webpackConfig,

        // test results reporter to use
        // possible values: 'dots', 'progress'
        // available reporters: https://npmjs.org/browse/keyword/karma-reporter
        reporters: ['spec'],


        // web server port
        port: 9876,


        // enable / disable colors in the output (reporters and logs)
        colors: true,


        // level of logging
        // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
        logLevel: config.LOG_INFO,


        // enable / disable watching file and executing tests whenever any file changes
        autoWatch: false,


        // start these browsers
        // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
        browsers: ['ChromeHeadless'],


        // Continuous Integration mode
        // if true, Karma captures browsers, runs the tests and exits
        singleRun: true,

        // Concurrency level
        // how many browser should be started simultaneous
        concurrency: Infinity
    })
};

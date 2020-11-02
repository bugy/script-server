module.exports = function (config) {
    config.set({
        testRunner: 'karma',
        karma: {
            config: {
                frameworks: ['mocha'],
                files: ['dist/*.js']
            }
        },
        tempDirName: '/tmp',
        mutate: ['src/common/components/terminal/terminal_model.js'],
        files: ['src/**/*.js', 'tests/unit/**/*.js'],
        mutator: 'javascript',
        coverageAnalysis: 'off',
        logLevel: 'info',
        transpilers: ['webpack'],
        webpack: {
            configFile: 'tests/mutation/stryker.webpack.config.js'
        },
        reporter: ['progress', 'clear-text', 'html'],
        htmlReporter: {baseDir: '/tmp/reports/stryker'}
    });
};
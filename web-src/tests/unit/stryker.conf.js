module.exports = function (config) {
    config.set({
        testRunner: 'karma',
        testFramework: 'mocha',
        karma: {
            project: 'custom',
            configFile: 'tests/karma.conf.js',
            config: {
                basePath: null,
                files: ['../../web/test_entry.js']
            }
        },
        tempDir: '/tmp',
        mutate: ['js/components/terminal/terminal_model.js'],
        mutator: 'javascript',
        coverageAnalysis: 'off',
        transpilers: ['webpack'],
        webpack: {
            configFile: 'webpack.mutation.js'
        },
        reporter: ['progress', 'clear-text', 'html']
    });
};
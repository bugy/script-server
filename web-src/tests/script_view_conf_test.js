"use strict";

var assert = chai.assert;
chai.config.truncateThreshold = 0;

describe('Test Configuration of ScriptView', function () {

    beforeEach(function () {
        this.viewContainer = document.createElement('div');
        document.children[0].appendChild(this.viewContainer);

        this.scriptView = new ScriptView(this.viewContainer);
        this.vueModel = this.scriptView.vueModel;
    });

    afterEach(function () {
        this.viewContainer.remove();
    });

    describe('Test descript section', function () {

        it('test simple text', function () {
            this.scriptView.setScriptDescription('some text');
            assert.equal('some text', this.vueModel.formattedDescription)
        });

        it('test bold', function () {
            this.scriptView.setScriptDescription('some **bold** text');
            assert.equal('some <strong>bold</strong> text', this.vueModel.formattedDescription)
        });

        it('test explicit link', function () {
            this.scriptView.setScriptDescription('some [link_text](https://google.com)');
            assert.equal('some <a href="https://google.com">link_text</a>', this.vueModel.formattedDescription)
        });

        it('test new line', function () {
            this.scriptView.setScriptDescription('line1\nline2');
            assert.equal('line1<br>line2', this.vueModel.formattedDescription)
        });
    })
});

'use strict';
import {createLocalVue, mount} from '@vue/test-utils';
import {assert, config as chaiConfig} from 'chai';
import Vuex from 'vuex';
import ScriptView from '../js/main-app/script-view';

chaiConfig.truncateThreshold = 0;

const localVue = createLocalVue();
localVue.use(Vuex);

describe('Test Configuration of ScriptView', function () {

    beforeEach(function () {
        const store = new Vuex.Store({
            modules: {
                scriptConfig: {
                    namespaced: true,
                    state: {
                        scriptConfig: {
                            description: ''
                        }
                    }
                }
            }
        });
        this.store = store;

        this.scriptView = mount(ScriptView, {
            attachToDocument: true,
            store,
            localVue
        });
    });

    afterEach(function () {
        this.scriptView.destroy();
    });

    describe('Test descript section', function () {

        it('test simple text', async function () {
            this.store.state.scriptConfig.scriptConfig.description = 'some text';
            assert.equal('some text', this.scriptView.vm.formattedDescription)
        });

        it('test bold', function () {
            this.store.state.scriptConfig.scriptConfig.description = 'some **bold** text';
            assert.equal('some <strong>bold</strong> text', this.scriptView.vm.formattedDescription)
        });

        it('test explicit link', function () {
            this.store.state.scriptConfig.scriptConfig.description = 'some [link_text](https://google.com)';
            assert.equal('some <a href="https://google.com">link_text</a>', this.scriptView.vm.formattedDescription)
        });

        it('test new line', function () {
            this.store.state.scriptConfig.scriptConfig.description = 'line1\nline2';
            assert.equal('line1<br>line2', this.scriptView.vm.formattedDescription)
        });
    })
});

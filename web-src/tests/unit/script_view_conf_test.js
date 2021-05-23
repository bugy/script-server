'use strict';
import ScriptView from '@/main-app/components/scripts/script-view';
import {mount} from '@vue/test-utils';
import Vuex from 'vuex';
import {attachToDocument, createScriptServerTestVue, vueTicks} from './test_utils';

const localVue = createScriptServerTestVue();
localVue.use(Vuex);

describe('Test Configuration of ScriptView', function () {
    let scriptView;

    beforeEach(function () {
        const store = new Vuex.Store({
            modules: {
                scriptConfig: {
                    namespaced: true,
                    state: {
                        scriptConfig: {
                            description: ''
                        },
                        loading: false
                    }
                }
            }
        });
        this.store = store;

        scriptView = mount(ScriptView, {
            attachTo: attachToDocument(),
            store,
            localVue
        });
    });

    afterEach(function () {
        scriptView.destroy();
    });

    describe('Test descript section', function () {

        it('test simple text', async function () {
            this.store.state.scriptConfig.scriptConfig.description = 'some text';
            expect(scriptView.vm.formattedDescription).toBe('some text')
        });

        it('test bold', function () {
            this.store.state.scriptConfig.scriptConfig.description = 'some **bold** text';
            expect(scriptView.vm.formattedDescription).toBe('some <strong>bold</strong> text')
        });

        it('test explicit link', function () {
            this.store.state.scriptConfig.scriptConfig.description = 'some [link_text](https://google.com)';
            expect(scriptView.vm.formattedDescription).toBe('some <a href="https://google.com">link_text</a>')
        });

        it('test new line', function () {
            this.store.state.scriptConfig.scriptConfig.description = 'line1\nline2';
            expect(scriptView.vm.formattedDescription).toBe('line1<br>line2')
        });
    });

    describe('Test loading', function () {

        it('test loading true when no config', async function () {
            this.store.state.scriptConfig.scriptConfig = null
            this.store.state.scriptConfig.loading = true

            await vueTicks();

            expect(scriptView.find('.script-loading-text').text()).toEqual('Loading ..')
            expect(scriptView.find('.button-execute').attributes('disabled')).toBe('disabled')
        });

        it('test loading true when config exists', async function () {
            this.store.state.scriptConfig.scriptConfig = {name: 'abc'}
            this.store.state.scriptConfig.loading = true

            await vueTicks();

            expect(scriptView.find('.script-loading-text').exists()).toBeFalse()
            expect(scriptView.find('.button-execute').attributes('disabled')).toBe('disabled')
        });

        it('test loading becomes false', async function () {
            this.store.state.scriptConfig.loading = true;

            await vueTicks();

            this.store.state.scriptConfig.loading = false;

            await vueTicks();

            expect(scriptView.find('.script-loading-text').exists()).toBeFalse();
            expect(scriptView.find('.button-execute').attributes('disabled')).toBeNil();
        });
    })
});

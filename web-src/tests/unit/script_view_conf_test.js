'use strict';
import ScriptView from '@/main-app/components/scripts/script-view';
import {mount} from '@vue/test-utils';
import {createStore as createVuexStore} from 'vuex';
import {attachToDocument, createScriptServerTestVue, vueTicks} from './test_utils';
describe('Test Configuration of ScriptView', function () {
    let scriptView;
    let store;

    beforeEach(function () {
        store = createVuexStore({
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

        scriptView = mount(ScriptView, {
            attachTo: attachToDocument(),
            global: {plugins: [store]},
        });
    });

    afterEach(function () {
        scriptView.unmount();
    });

    describe('Test descript section', function () {

        it('test simple text', async function () {
            store.state.scriptConfig.scriptConfig.description = 'some text';
            expect(scriptView.vm.formattedDescription).toBe('some text')
        });

        it('test bold', function () {
            store.state.scriptConfig.scriptConfig.description = 'some **bold** text';
            expect(scriptView.vm.formattedDescription).toBe('some <strong>bold</strong> text')
        });

        it('test explicit link', function () {
            store.state.scriptConfig.scriptConfig.description = 'some [link_text](https://google.com)';
            expect(scriptView.vm.formattedDescription).toBe('some <a href="https://google.com">link_text</a>')
        });

        it('test new line', function () {
            store.state.scriptConfig.scriptConfig.description = 'line1\nline2';
            expect(scriptView.vm.formattedDescription).toBe('line1<br>line2')
        });
    });

    describe('Test loading', function () {

        it('test loading true when no config', async function () {
            store.state.scriptConfig.scriptConfig = null
            store.state.scriptConfig.loading = true

            await vueTicks();

            expect(scriptView.find('.script-loading-text').text()).toEqual('Loading ..')
            expect(scriptView.find('.button-execute').attributes('disabled')).toBe('')
        });

        it('test loading true when config exists', async function () {
            store.state.scriptConfig.scriptConfig = {name: 'abc'}
            store.state.scriptConfig.loading = true

            await vueTicks();

            expect(scriptView.find('.script-loading-text').exists()).toBeFalse()
            expect(scriptView.find('.button-execute').attributes('disabled')).toBe('')
        });

        it('test loading becomes false', async function () {
            store.state.scriptConfig.loading = true;

            await vueTicks();

            store.state.scriptConfig.loading = false;

            await vueTicks();

            expect(scriptView.find('.script-loading-text').exists()).toBeFalse();
            expect(scriptView.find('.button-execute').attributes('disabled')).toBeNil();
        });
    })
});

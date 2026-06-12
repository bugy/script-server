'use strict';
import ScriptView from '@/main-app/components/scripts/script-view';
import {mount} from '@vue/test-utils';
import {createPinia, setActivePinia} from 'pinia';
import {useScriptConfigStore} from '@/main-app/stores/scriptConfig';
import {attachToDocument, createScriptServerTestVue, vueTicks} from './test_utils';

describe('Test Configuration of ScriptView', function () {
    let scriptView;
    let pinia;

    beforeEach(function () {
        pinia = createPinia();
        setActivePinia(pinia);

        const scriptConfigStore = useScriptConfigStore();
        scriptConfigStore.scriptConfig = {description: ''};
        scriptConfigStore.loading = false;

        scriptView = mount(ScriptView, {
            attachTo: attachToDocument(),
            global: {plugins: [pinia]},
        });
    });

    afterEach(function () {
        scriptView.unmount();
    });

    describe('Test descript section', function () {

        it('test simple text', async function () {
            useScriptConfigStore().scriptConfig.description = 'some text';
            expect(scriptView.vm.formattedDescription).toBe('some text')
        });

        it('test bold', function () {
            useScriptConfigStore().scriptConfig.description = 'some **bold** text';
            expect(scriptView.vm.formattedDescription).toBe('some <strong>bold</strong> text')
        });

        it('test explicit link', function () {
            useScriptConfigStore().scriptConfig.description = 'some [link_text](https://google.com)';
            expect(scriptView.vm.formattedDescription).toBe('some <a href="https://google.com">link_text</a>')
        });

        it('test new line', function () {
            useScriptConfigStore().scriptConfig.description = 'line1\nline2';
            expect(scriptView.vm.formattedDescription).toBe('line1<br>line2')
        });
    });

    describe('Test loading', function () {

        it('test loading true when no config', async function () {
            useScriptConfigStore().scriptConfig = null;
            useScriptConfigStore().loading = true;

            await vueTicks();

            expect(scriptView.find('.script-loading-text').text()).toEqual('Loading ..')
            expect(scriptView.find('.button-execute').attributes('disabled')).toBe('')
        });

        it('test loading true when config exists', async function () {
            useScriptConfigStore().scriptConfig = {name: 'abc'};
            useScriptConfigStore().loading = true;

            await vueTicks();

            expect(scriptView.find('.script-loading-text').exists()).toBeFalse()
            expect(scriptView.find('.button-execute').attributes('disabled')).toBe('')
        });

        it('test loading becomes false', async function () {
            useScriptConfigStore().loading = true;

            await vueTicks();

            useScriptConfigStore().loading = false;

            await vueTicks();

            expect(scriptView.find('.script-loading-text').exists()).toBeFalse();
            expect(scriptView.find('.button-execute').attributes('disabled')).toBeNil();
        });
    })
});

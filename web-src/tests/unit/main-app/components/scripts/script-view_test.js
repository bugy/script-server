'use strict';
import ScriptView from '@/main-app/components/scripts/script-view';
import {mount} from '@vue/test-utils';
import {createPinia, setActivePinia} from 'pinia';
import {useScriptConfigStore} from '@/main-app/stores/scriptConfig';
import {useExecutionsStore} from '@/main-app/stores/executions';
import {useScriptsStore} from '@/main-app/stores/scripts';
import {attachToDocument, createScriptServerTestVue} from '../../../test_utils'

describe('Test ScriptView', function () {
    let scriptView;
    let pinia;

    beforeEach(async function () {
        pinia = createPinia();
        setActivePinia(pinia);

        const scriptConfigStore = useScriptConfigStore();
        scriptConfigStore.scriptConfig = {description: ''};
        scriptConfigStore.loading = false;

        useScriptsStore().selectedScript = 'abc';

        // Stub selectExecutor to prevent side-effects
        const executionsStore = useExecutionsStore();
        vi.spyOn(executionsStore, 'selectExecutor').mockImplementation((executor) => {
            executionsStore.currentExecutor = executor;
        });

        scriptView = mount(ScriptView, {
            attachTo: attachToDocument(),
            global: {plugins: [pinia]},
        });
        await scriptView.vm.$nextTick();
    });

    afterEach(function () {
        scriptView.unmount();
        vi.restoreAllMocks();
    });

    describe('Test log content', function () {
        it('test init with logs', async function () {
            useExecutionsStore().currentExecutor = {
                state: {
                    id: 1,
                    scriptName: 'my script',
                    logChunks: ['a', 'b', 'c'],
                    inputPromptText: '',
                    inlineImages: {}
                }
            };

            const newScriptView = mount(ScriptView, {
                attachTo: attachToDocument(),
                global: {plugins: [pinia]},
            });
            await newScriptView.vm.$nextTick();

            try {
                const logText = newScriptView.get('.log-content').text();
                expect(logText).toEqual('abc');

            } finally {
                newScriptView.unmount();
            }
        });
    });
});

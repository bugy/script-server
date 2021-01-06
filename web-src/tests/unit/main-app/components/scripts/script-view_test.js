'use strict';
import ScriptView from '@/main-app/components/scripts/script-view';
import {mount} from '@vue/test-utils';
import Vuex from 'vuex';
import {createScriptServerTestVue} from '../../../test_utils'

const localVue = createScriptServerTestVue();
localVue.use(Vuex);


describe('Test ScriptView', function () {
    let scriptView;
    let store;

    beforeEach(async function () {
        store = new Vuex.Store({
            modules: {
                scripts: {
                    namespaced: true,
                    state: {
                        selectedScript: 'abc'
                    }
                },
                scriptConfig: {
                    namespaced: true,
                    state: {
                        scriptConfig: {
                            description: ''
                        },
                        loading: false
                    }
                },
                executions: {
                    namespaced: true,
                    state: {
                        currentExecutor: null,
                        executors: {}
                    },
                    actions: {
                        selectExecutor({state}, executor) {
                            state.currentExecutor = executor;
                        }
                    }
                }
            }
        });

        scriptView = mount(ScriptView, {
            attachToDocument: true,
            store,
            localVue
        });

        scriptView.vm.$parent.$forceUpdate();
        await scriptView.vm.$nextTick();
    });

    afterEach(function () {
        scriptView.destroy();
    });

    describe('Test log content', function () {
        it('test init with logs', async function () {
            store.state.executions.currentExecutor = {
                state: {
                    id: 1,
                    scriptName: 'my script',
                    logChunks: ['a', 'b', 'c'],
                    inputPromptText: '',
                    inlineImages: {}
                }
            };

            const newScriptView = mount(ScriptView, {
                attachToDocument: true,
                store,
                localVue
            });

            newScriptView.vm.$parent.$forceUpdate();
            await newScriptView.vm.$nextTick();

            try {
                const logText = newScriptView.get('.log-content').text();
                expect(logText).toEqual('abc');

            } finally {
                newScriptView.destroy();
            }
        });
    });
});

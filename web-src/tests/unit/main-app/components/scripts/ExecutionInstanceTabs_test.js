'use strict';
import ExecutionInstanceTabs from '@/main-app/components/scripts/ExecutionInstanceTabs';
import {mount} from '@vue/test-utils';
import clone from 'lodash/clone';
import Vuex from 'vuex';
import {attachToDocument, createScriptServerTestVue, vueTicks} from '../../../test_utils';

const localVue = createScriptServerTestVue();
localVue.use(Vuex);


describe('Test ExecutionInstanceTabs', function () {
    let executionTabs;
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

        executionTabs = mount(ExecutionInstanceTabs, {
            attachTo: attachToDocument(),
            store,
            localVue
        });

        executionTabs.vm.$parent.$forceUpdate();
        await executionTabs.vm.$nextTick();
    });

    afterEach(function () {
        executionTabs.destroy();
    });

    async function addExecutor(id, scriptName, status = 'running') {
        const executors = clone(store.state.executions.executors);
        executors[id] = {state: {id, scriptName, status}}

        store.state.executions.executors = executors;

        await vueTicks();
    }

    async function removeExecutor(id) {
        const executors = clone(store.state.executions.executors);
        delete executors[id];

        store.state.executions.executors = executors;

        await vueTicks();
    }

    async function selectExecutor(id) {
        const executor = store.state.executions.executors[id];
        expect(executor).not.toBeNil();

        store.state.executions.currentExecutor = executor;

        await vueTicks();
    }

    async function selectScript(scriptName) {
        store.state.scripts.selectedScript = scriptName;

        await vueTicks();
    }

    function assertTab(tab, id, status, selected) {
        let expectedText
        switch (status) {
            case 'finished':
                expectedText = 'check'
                break
            case 'disconnected':
            case 'error':
                expectedText = 'error_outline'
                break
            default:
                expectedText = 'lens'
        }
        expectedText += id;

        expect(tab.text()).toBe(expectedText);

        const tabButton = tab.get('a');
        if (selected) {
            expect(tabButton.classes()).toContain('active');
        } else {
            expect(tabButton.classes()).not.toContain('active');
        }
    }

    describe('Test script tabs', function () {

        it('test single inactive tab', async function () {
            await addExecutor(123, 'abc')

            const tabs = executionTabs.findAll('li.executor-tab');
            expect(tabs).toHaveLength(1);
            assertTab(tabs.at(0), 123, 'running', false);
        });

        it('test single active tab', async function () {
            await addExecutor(123, 'abc')
            await selectExecutor(123);

            const tabs = executionTabs.findAll('li.executor-tab');
            expect(tabs).toHaveLength(1);
            assertTab(tabs.at(0), 123, 'running', true);
        });

        it('test multiple tabs', async function () {
            await addExecutor(101, 'abc');
            await addExecutor(103, 'def');
            await addExecutor(105, 'abc', status = 'finished');
            await addExecutor(106, 'ghi');
            await addExecutor(107, 'abc');
            await addExecutor(108, 'xyz');
            await addExecutor(109, 'abc', status = 'disconnected');
            await addExecutor(110, 'abc', status = 'error');
            await selectExecutor(105);

            const tabs = executionTabs.findAll('li.executor-tab');
            expect(tabs).toHaveLength(5);

            assertTab(tabs.at(0), 101, 'running', false);
            assertTab(tabs.at(1), 105, 'finished', true);
            assertTab(tabs.at(2), 107, 'running', false);
            assertTab(tabs.at(3), 109, 'error', false);
            assertTab(tabs.at(4), 110, 'error', false);
        });

        it('test multiple tabs after changing script', async function () {
            await addExecutor(101, 'abc');
            await addExecutor(103, 'def', status = 'finished');
            await addExecutor(105, 'abc', status = 'finished');
            await addExecutor(106, 'ghi');
            await addExecutor(107, 'abc');
            await addExecutor(108, 'def');
            await selectExecutor(103);
            await selectScript('def');

            const tabs = executionTabs.findAll('li.executor-tab');
            expect(tabs).toHaveLength(2);

            assertTab(tabs.at(0), 103, 'finished', true);
            assertTab(tabs.at(1), 108, 'running', false);
        });

        it('test no tabs', async function () {
            expect(executionTabs.isEmpty()).toBeTrue();
        });
    })

    describe('Test add tab button', function () {

        it('test add button when single executor', async function () {
            await addExecutor(123, 'abc')
            await selectExecutor(123);

            const tabs = executionTabs.findAll('li');
            expect(tabs).toHaveLength(2);
            expect(tabs.at(1).text()).toBe('add');
            expect(tabs.at(1).get('a').classes()).not.toContain('active');
        });

        it('test add button when multiple executors', async function () {
            await addExecutor(101, 'abc')
            await addExecutor(102, 'abc')
            await addExecutor(103, 'abc')
            await selectExecutor(102);

            const tabs = executionTabs.findAll('li');
            expect(tabs).toHaveLength(4);
            expect(tabs.at(3).text()).toBe('add');
        });

        it('test add button when multiple executors for different script', async function () {
            await addExecutor(101, 'def')
            await addExecutor(102, 'xyz')
            await addExecutor(103, 'hello')

            const tabs = executionTabs.findAll('li');
            expect(tabs).toHaveLength(0);
        });

        it('test add button when active', async function () {
            await addExecutor(101, 'abc')

            store.state.executions.currentExecutor = null;

            await vueTicks();

            const addButton = executionTabs.get('.add-execution-tab-button');
            expect(addButton.classes()).toContain('active');
        });
    });

    describe('Test click tabs', function () {

        it('test click executor tab when nothing selected', async function () {
            await addExecutor(123, 'abc')

            const firstTabButton = executionTabs.findAll('li a').at(0);
            firstTabButton.trigger('click');

            expect(store.state.executions.currentExecutor.state.id).toBe(123);
        });


        it('test click executor tab when another selected', async function () {
            await addExecutor(101, 'abc')
            await addExecutor(102, 'abc')
            await selectExecutor(101)

            const secondTabButton = executionTabs.findAll('li a').at(1);
            secondTabButton.trigger('click');

            expect(store.state.executions.currentExecutor.state.id).toBe(102);
        });

        it('test click add tab when another selected', async function () {
            await addExecutor(101, 'abc')
            await addExecutor(102, 'abc')
            await selectExecutor(101)

            const addButton = executionTabs.get('.add-execution-tab-button');
            addButton.trigger('click');

            expect(store.state.executions.currentExecutor).toBeNil();
        });
    });

    describe('Test indicator position', function () {

        function assertIndicatorAtTab(indicator, firstTab) {
            expect(indicator.offsetLeft).toBe(firstTab.offsetLeft);
            expect(indicator.offsetWidth).toBe(firstTab.offsetWidth);
        }

        it('test indicator when first executor', async function () {
            await addExecutor(101, 'abc');
            await addExecutor(102, 'abc');
            await addExecutor(103, 'abc');
            await selectExecutor(101);

            const indicator = executionTabs.get('.tab-indicator');
            const firstTab = executionTabs.findAll('.tab').at(0);

            assertIndicatorAtTab(indicator, firstTab);
        });

        it('test indicator when last executor', async function () {
            await addExecutor(101, 'abc');
            await addExecutor(102, 'abc');
            await addExecutor(103, 'abc');
            await selectExecutor(103);

            const indicator = executionTabs.get('.tab-indicator');
            const lastTab = executionTabs.findAll('.tab').at(2);

            assertIndicatorAtTab(indicator, lastTab);
        });

        it('test indicator when nothing selected', async function () {
            await addExecutor(101, 'abc');
            await addExecutor(102, 'abc');
            await addExecutor(103, 'abc');

            const indicator = executionTabs.get('.tab-indicator');
            const addTab = executionTabs.findAll('.tab').at(3);

            assertIndicatorAtTab(indicator, addTab);
        });

        it('test indicator position after remove selected', async function () {
            await addExecutor(101, 'abc');
            await addExecutor(102, 'abc');
            await addExecutor(103, 'abc');
            await selectExecutor(103);

            store.state.executions.currentExecutor = null;

            await vueTicks();

            const indicator = executionTabs.get('.tab-indicator');
            const addTab = executionTabs.findAll('.tab').at(3);

            assertIndicatorAtTab(indicator, addTab);
        });

        it('test indicator position after changing executors', async function () {
            await addExecutor(101, 'abc');
            await addExecutor(102, 'abc');
            await addExecutor(103, 'abc');
            await selectExecutor(103);
            await removeExecutor(102);

            const indicator = executionTabs.get('.tab-indicator');
            const lastTab = executionTabs.findAll('.tab').at(1);

            assertIndicatorAtTab(indicator, lastTab);
        });
    });

});

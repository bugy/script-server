'use strict';

import {hasClass, isBlankString} from '@/common/utils/common';
import ScriptsList from '@/main-app/components/scripts/ScriptsList';
import router from '@/main-app/router/router';
import {mount} from '@vue/test-utils';
import VueRouter from 'vue-router';
import Vuex from 'vuex';
import {attachToDocument, createScriptServerTestVue, triggerSingleClick, vueTicks} from '../../test_utils';

const localVue = createScriptServerTestVue();
localVue.use(Vuex);
localVue.use(VueRouter);

describe('Test ScriptConfig', function () {
    let store;
    let listComponent;

    beforeEach(async function () {
        store = new Vuex.Store({
            modules: {
                scripts: {
                    namespaced: true,
                    state: {
                        scripts: [],
                        selectedScript: null
                    }
                },
                executions: {
                    executors: {}
                }
            }
        });

        listComponent = mount(ScriptsList, {
            store,
            localVue,
            router,
            attachTo: attachToDocument()
        });

        await vueTicks();
    });

    afterEach(async function () {
        await vueTicks();

        listComponent.destroy();
    });

    function getText(item) {
        return Array.from(item.childNodes)
            .filter(child => child.nodeType === 3)
            .map(child => child.nodeValue.trim())
            .reduce((left, right) => left + right);
    }

    function getGroupText(groupItem) {
        let groupTextItem = $(groupItem).find('> .script-group > span').get(0);
        return getText(groupTextItem);
    }

    function getTopLevelItems() {
        return Array.from(listComponent.vm.$el.childNodes)
            .filter(child => hasClass(child, 'collection-item') || hasClass(child, 'script-list-group'))
            .map(child => {
                if (hasClass(child, 'script-list-group')) {
                    return getGroupText(child);
                }

                return getText(child);
            });
    }

    function findGroupItem(groupName) {
        let foundGroups = $(listComponent.vm.$el)
            .find('.script-list-group')
            .has('.script-group > span:contains("' + groupName + '")')
            .toArray()

        expect(foundGroups).toBeArrayOfSize(1)
        return foundGroups[0];
    }

    function assertGroupItems(groupName, expectedTexts) {
        let foundGroup = findGroupItem(groupName);

        let innerItems = $(foundGroup).find('.collection-item:not(.script-group)').toArray();
        let actualTexts = innerItems.map(item => getText(item));
        expect(actualTexts).toEqual(expectedTexts)
    }

    function assertOpenGroup(expectedOpenGroup, expectedItems) {
        if (!isBlankString(expectedOpenGroup)) {
            assertGroupItems(expectedOpenGroup, expectedItems);
        }

        let groupItems = $(listComponent.vm.$el).find('.script-list-group').toArray();
        for (const groupItem of groupItems) {
            let itemName = getGroupText(groupItem);
            if (itemName === expectedOpenGroup) {
                continue;
            }

            assertGroupItems(itemName, []);
        }
    }

    async function clickOnGroup(groupName) {
        let dropdownItem = $(findGroupItem(groupName)).find('.script-group');
        triggerSingleClick(dropdownItem.get(0));

        await vueTicks();
    }

    describe('Test show list', function () {
        it('Test show single item', async function () {
            store.state.scripts.scripts = [{'name': 'abc'}];

            await vueTicks();

            let texts = getTopLevelItems();

            expect(texts).toEqual(['abc'])
        });

        it('Test show multiple items', async function () {
            store.state.scripts.scripts = [{'name': 'abc'}, {'name': 'xyz'}, {'name': 'def'}];

            await vueTicks();

            let texts = getTopLevelItems();

            expect(texts).toEqual(['abc', 'def', 'xyz'])
        });

        it('Test show single item in group', async function () {
            store.state.scripts.scripts = [{'name': 'abc', 'group': 'g1'}];

            await vueTicks();

            let texts = getTopLevelItems();

            expect(texts).toEqual(['g1'])
        });

        it('Test show multiple items in different groups', async function () {
            store.state.scripts.scripts = [
                {'name': 'abc', 'group': 'g3'},
                {'name': 'xyz', 'group': 'g2'},
                {'name': 'def', 'group': 'g1'}];

            await vueTicks();

            let texts = getTopLevelItems();

            expect(texts).toEqual(['g1', 'g2', 'g3'])
        });

        it('Test show multiple items in different groups when empty', async function () {
            store.state.scripts.scripts = [
                {'name': 'abc', 'group': null},
                {'name': 'xyz', 'group': ''},
                {'name': 'def', 'group': ' \n'}];

            await vueTicks();

            let texts = getTopLevelItems();

            expect(texts).toEqual(['abc', 'def', 'xyz'])
        });

        it('Test show multiple items in same groups', async function () {
            store.state.scripts.scripts = [
                {'name': 'abc', 'group': 'g3'},
                {'name': 'ghi', 'group': 'g1'},
                {'name': 'xyz', 'group': 'g2'},
                {'name': 'jkl', 'group': 'g2'},
                {'name': 'def', 'group': 'g1'}];

            await vueTicks();

            let texts = getTopLevelItems();

            expect(texts).toEqual(['g1', 'g2', 'g3'])
        });

        it('Test show items and groups mixed', async function () {
            store.state.scripts.scripts = [
                {'name': 'abc', 'group': 'g3'},
                {'name': 'ghi'},
                {'name': 'xyz', 'group': 'g2'},
                {'name': 'jkl', 'group': 'g2'},
                {'name': 'def'}];

            await vueTicks();

            let texts = getTopLevelItems();

            expect(texts).toEqual(['def', 'g2', 'g3', 'ghi'])
        });
    });

    describe('Test open groups', function () {
        it('Test nothing open by default', async function () {
            store.state.scripts.scripts = [
                {'name': 'abc', 'group': 'g3'},
                {'name': 'xyz', 'group': 'g2'},
                {'name': 'def', 'group': 'g1'}];

            await vueTicks();

            assertOpenGroup(null);
        });

        it('Test open by default when selected', async function () {
            store.state.scripts.scripts = [
                {'name': 'abc', 'group': 'g3'},
                {'name': 'xyz', 'group': 'g2'},
                {'name': 'def', 'group': 'g1'}];
            store.state.scripts.selectedScript = 'abc';

            await vueTicks();

            assertOpenGroup('g3', ['abc']);
        });

        it('Test open on click', async function () {
            store.state.scripts.scripts = [
                {'name': 'abc', 'group': 'g3'},
                {'name': 'def', 'group': 'g2'},
                {'name': 'xyz', 'group': 'g2'}];

            await vueTicks();
            await clickOnGroup('g2');

            assertOpenGroup('g2', ['def', 'xyz']);
        });

        it('Test open another group on click', async function () {
            store.state.scripts.scripts = [
                {'name': 'abc', 'group': 'g3'},
                {'name': 'def', 'group': 'g2'},
                {'name': 'xyz', 'group': 'g2'}];

            await vueTicks();
            await clickOnGroup('g2');
            await clickOnGroup('g3');

            assertOpenGroup('g3', ['abc']);
        });

        it('Test close group on second click', async function () {
            store.state.scripts.scripts = [
                {'name': 'abc', 'group': 'g3'},
                {'name': 'def', 'group': 'g2'},
                {'name': 'xyz', 'group': 'g2'}];

            await vueTicks();
            await clickOnGroup('g2');
            await clickOnGroup('g2');

            assertOpenGroup(null);
        });

    });
});
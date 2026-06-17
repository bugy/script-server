'use strict';

import ScriptsList from '@/main-app/components/scripts/ScriptsList';
import router from '@/main-app/router/router';
import {mount} from '@vue/test-utils';
import {createPinia, setActivePinia} from 'pinia';
import {useScriptsStore} from '@/main-app/stores/scripts';
import {attachToDocument, triggerSingleClick, vueTicks} from '../../test_utils';

describe('Test ScriptConfig', function () {
    let pinia;
    let scriptsStore;
    let listComponent;

    beforeEach(async function () {
        pinia = createPinia();
        setActivePinia(pinia);

        scriptsStore = useScriptsStore();
        scriptsStore.scripts = [];
        scriptsStore.selectedScript = null;

        listComponent = mount(ScriptsList, {
            global: {plugins: [pinia, router]},
            attachTo: attachToDocument()
        });

        await vueTicks();
    });

    afterEach(async function () {
        await vueTicks();

        listComponent.unmount();
    });

    function getGroupTitle(groupEl) {
        const titleEl = groupEl.querySelector('.v-list-group__header .v-list-item-title');
        return titleEl ? titleEl.textContent.trim() : '';
    }

    function getItemTitle(itemEl) {
        const titleEl = itemEl.querySelector('.v-list-item-title');
        return titleEl ? titleEl.textContent.trim() : '';
    }

    function getTopLevelItems() {
        return Array.from(listComponent.vm.$el.children)
            .filter(child => child.classList.contains('v-list-item') || child.classList.contains('v-list-group'))
            .map(child => {
                if (child.classList.contains('v-list-group')) {
                    return getGroupTitle(child);
                }
                return getItemTitle(child);
            });
    }

    function findGroupElement(groupName) {
        const groups = [...listComponent.vm.$el.querySelectorAll('.v-list-group')]
            .filter(g => getGroupTitle(g) === groupName);
        expect(groups).toBeArrayOfSize(1);
        return groups[0];
    }

    function isGroupOpen(groupEl) {
        return groupEl.classList.contains('v-list-group--open');
    }

    function assertGroupItems(groupName, expectedTexts) {
        const groupEl = findGroupElement(groupName);
        const itemsContainer = groupEl.querySelector('.v-list-group__items');
        if (!expectedTexts.length) {
            expect(itemsContainer).toBeFalsy();
            return;
        }
        expect(itemsContainer).toBeTruthy();
        const items = [...itemsContainer.querySelectorAll('.v-list-item')];
        const texts = items.map(item => getItemTitle(item));
        expect(texts).toEqual(expectedTexts);
    }

    function assertOpenGroup(expectedOpenGroup, expectedItems) {
        const groupEls = [...listComponent.vm.$el.querySelectorAll('.v-list-group')];
        for (const groupEl of groupEls) {
            const name = getGroupTitle(groupEl);
            if (name === expectedOpenGroup) {
                expect(isGroupOpen(groupEl)).toBe(true);
                if (expectedItems) {
                    assertGroupItems(name, expectedItems);
                }
            } else {
                expect(isGroupOpen(groupEl)).toBe(false);
            }
        }
    }

    async function clickOnGroup(groupName) {
        const groupEl = findGroupElement(groupName);
        const header = groupEl.querySelector('.v-list-group__header');
        triggerSingleClick(header);
        await vueTicks();
    }

    describe('Test show list', function () {
        it('Test show single item', async function () {
            scriptsStore.scripts = [{'name': 'abc'}];

            await vueTicks();

            let texts = getTopLevelItems();

            expect(texts).toEqual(['abc'])
        });

        it('Test show multiple items', async function () {
            scriptsStore.scripts = [{'name': 'abc'}, {'name': 'xyz'}, {'name': 'def'}];

            await vueTicks();

            let texts = getTopLevelItems();

            expect(texts).toEqual(['abc', 'def', 'xyz'])
        });

        it('Test show single item in group', async function () {
            scriptsStore.scripts = [{'name': 'abc', 'group': 'g1'}];

            await vueTicks();

            let texts = getTopLevelItems();

            expect(texts).toEqual(['g1'])
        });

        it('Test show multiple items in different groups', async function () {
            scriptsStore.scripts = [
                {'name': 'abc', 'group': 'g3'},
                {'name': 'xyz', 'group': 'g2'},
                {'name': 'def', 'group': 'g1'}];

            await vueTicks();

            let texts = getTopLevelItems();

            expect(texts).toEqual(['g1', 'g2', 'g3'])
        });

        it('Test show multiple items in different groups when empty', async function () {
            scriptsStore.scripts = [
                {'name': 'abc', 'group': null},
                {'name': 'xyz', 'group': ''},
                {'name': 'def', 'group': ' \n'}];

            await vueTicks();

            let texts = getTopLevelItems();

            expect(texts).toEqual(['abc', 'def', 'xyz'])
        });

        it('Test show multiple items in same groups', async function () {
            scriptsStore.scripts = [
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
            scriptsStore.scripts = [
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
            scriptsStore.scripts = [
                {'name': 'abc', 'group': 'g3'},
                {'name': 'xyz', 'group': 'g2'},
                {'name': 'def', 'group': 'g1'}];

            await vueTicks();

            assertOpenGroup(null);
        });

        it('Test open by default when selected', async function () {
            scriptsStore.scripts = [
                {'name': 'abc', 'group': 'g3'},
                {'name': 'xyz', 'group': 'g2'},
                {'name': 'def', 'group': 'g1'}];
            scriptsStore.selectedScript = 'abc';

            await vueTicks();

            assertOpenGroup('g3', ['abc']);
        });

        it('Test open on click', async function () {
            scriptsStore.scripts = [
                {'name': 'abc', 'group': 'g3'},
                {'name': 'def', 'group': 'g2'},
                {'name': 'xyz', 'group': 'g2'}];

            await vueTicks();
            await clickOnGroup('g2');

            assertOpenGroup('g2', ['def', 'xyz']);
        });

        it('Test open another group on click', async function () {
            scriptsStore.scripts = [
                {'name': 'abc', 'group': 'g3'},
                {'name': 'def', 'group': 'g2'},
                {'name': 'xyz', 'group': 'g2'}];

            await vueTicks();
            await clickOnGroup('g2');
            await clickOnGroup('g3');

            assertOpenGroup('g3', ['abc']);
        });

        it('Test close group on second click', async function () {
            scriptsStore.scripts = [
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

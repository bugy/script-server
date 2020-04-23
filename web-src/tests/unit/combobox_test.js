'use strict';

import Combobox from '@/common/components/combobox'
import {contains} from '@/common/utils/common';
import {mount} from '@vue/test-utils';
import {setDeepProp, timeout, triggerSingleClick, vueTicks, wrapVModel} from './test_utils';


describe('Test ComboBox', function () {
    let comboBox;

    beforeEach(async function () {
        comboBox = mount(Combobox, {
            attachToDocument: true,
            propsData: {
                config: {
                    required: false,
                    name: 'List param X',
                    description: 'some param',
                    values: ['Value A', 'Value B', 'Value C'],
                    multiselect: false
                },
                value: 'Value B'
            }
        });
        comboBox.vm.$parent.$forceUpdate();
        await comboBox.vm.$nextTick();

        wrapVModel(comboBox);
    });

    afterEach(async function () {
        await vueTicks();
        comboBox.destroy();
    });

    function assertListElements(expectedTexts, searchHeader = false) {
        const listChildren = comboBox.findAll('li');
        expect(listChildren).toHaveLength(expectedTexts.length + 1);

        const headerText = listChildren.at(0).text();
        if (!searchHeader) {
            expect(headerText).toBe('Choose your option');
        } else {
            expect(headerText.trim()).toBe('Search');
        }

        for (let i = 0; i < expectedTexts.length; i++) {
            const value = expectedTexts[i];
            expect(listChildren.at(i + 1).text()).toBe(value);
        }
    }

    async function openDropdown() {
        comboBox.get('.dropdown-trigger').trigger('click');

        await timeout(50);
    }

    function findSelectedOptions() {
        return comboBox.findAll('option').filter(option => option.element.selected);
    }

    describe('Test config', function () {

        it('Test initial name', function () {
            expect(comboBox.get('select').attributes('id')).toBe('List param X');
            expect(comboBox.get('label').text()).toBe('List param X');
        });

        it('Test change name', async function () {
            setDeepProp(comboBox, 'config.name', 'testName1');

            await vueTicks();

            expect(comboBox.get('select').attributes('id')).toBe('testName1');
            expect(comboBox.get('label').text()).toBe('testName1');
        });

        it('Test initial required', function () {
            expect(comboBox.get('select').attributes('required')).toBeFalsy();
        });

        it('Test change required', async function () {
            setDeepProp(comboBox, 'config.required', true);

            await vueTicks();

            expect(comboBox.get('select').attributes('required')).toBe('required');
        });

        it('Test initial description', function () {
            expect(comboBox.element.title).toBe('some param');
        });

        it('Test change description', async function () {
            setDeepProp(comboBox, 'config.description', 'My new desc');

            await vueTicks();

            expect(comboBox.element.title).toBe('My new desc');
        });

        it('Test initial multiselect', function () {
            expect(comboBox.find('select').attributes('multiple')).toBeNil();

            const listElement = comboBox.get('ul');
            expect(listElement.classes()).not.toContain('multiple-select-dropdown');
        });


        it('Test initial allowed values', function () {
            const values = ['Value A', 'Value B', 'Value C'];

            assertListElements(values);
        });

        it('Test change allowed values', async function () {
            const values = ['val1', 'val2', 'hello', 'another option'];
            setDeepProp(comboBox, 'config.values', values);

            await vueTicks();

            assertListElements(values);
        });
    });

    describe('Test values', function () {

        it('Test initial value', async function () {
            await vueTicks();

            expect(comboBox.vm.value).toBe('Value B');

            const selectedOption = comboBox.find('.selected').text();
            expect(selectedOption).toBe('Value B');
        });

        it('Test external value change', async function () {
            comboBox.setProps({value: 'Value C'});

            await vueTicks();

            expect(comboBox.vm.value).toBe('Value C');

            const selectedOption = comboBox.get('.selected').text();
            expect(selectedOption).toBe('Value C');
        });

        it('Test select another value', async function () {
            comboBox.get('select').setValue('Value A');

            await vueTicks();

            expect(comboBox.vm.value).toBe('Value A');

            const selectedOption = comboBox.get('.selected').text();
            expect(selectedOption).toBe('Value A');
        });

        it('Test set unknown value', async function () {
            comboBox.setProps({value: 'Xyz'});

            await vueTicks();

            expect(comboBox.vm.value).toBeNull();
            expect(findSelectedOptions()).toHaveLength(1);
            expect(comboBox.get('.selected').text()).toBe('Choose your option');
        });

        it('Test set multiselect single value', async function () {
            setDeepProp(comboBox, 'config.multiselect', true);
            await vueTicks();

            comboBox.setProps({value: 'Value A'});

            await vueTicks();
            expect(comboBox.vm.value).toEqual(['Value A']);
            expect(comboBox.get('.selected').text()).toBe('Value A');
        });

        it('Test set multiselect multiple values', async function () {
            setDeepProp(comboBox, 'config.multiselect', true);
            await vueTicks();

            comboBox.setProps({value: ['Value A', 'Value C']});

            await vueTicks();
            expect(comboBox.vm.value).toEqual(['Value A', 'Value C']);

            const selectedElements = findSelectedOptions();
            expect(selectedElements).toHaveLength(2);
            expect(selectedElements.at(0).text()).toBe('Value A');
            expect(selectedElements.at(1).text()).toBe('Value C');
        });

        it('Test set multiselect single unknown value', async function () {
            setDeepProp(comboBox, 'config.multiselect', true);
            await vueTicks();

            comboBox.setProps({value: ['Value X']});

            await vueTicks();
            expect(comboBox.vm.value).toEqual([]);
            expect(comboBox.get('.selected').text()).toBe('Choose your option');
        });

        it('Test set multiselect unknown value from multiple', async function () {
            setDeepProp(comboBox, 'config.multiselect', true);
            await vueTicks();

            comboBox.setProps({value: ['Value A', 'Value X']});

            await vueTicks();
            expect(comboBox.vm.value).toEqual(['Value A']);
            expect(comboBox.get('.selected').text()).toBe('Value A');
        });

        it('Test select multiple values in multiselect', async function () {
            setDeepProp(comboBox, 'config.multiselect', true);
            await vueTicks();

            const values = ['Value A', 'Value C'];
            const selectElement = $(comboBox.get('select').element);
            selectElement.val(values);
            selectElement.trigger('change');

            await vueTicks();

            expect(comboBox.vm.value).toEqual(values);

            const selectedElements = findSelectedOptions();
            expect(selectedElements).toHaveLength(2);
            expect(selectedElements.at(0).text()).toBe('Value A');
            expect(selectedElements.at(1).text()).toBe('Value C');
        });

        it('Test change allowed values with matching value', async function () {
            setDeepProp(comboBox, 'config.values', ['val1', 'val2', 'hello', 'Value B', 'another option']);

            await vueTicks();

            expect(comboBox.vm.value).toBe('Value B');
            expect(comboBox.get('.selected').text()).toBe('Value B');
        });

        it('Test change allowed values with unmatching value', async function () {
            setDeepProp(comboBox, 'config.values', ['val1', 'val2', 'hello', 'another option']);

            await vueTicks();

            expect(comboBox.vm.value).toBeNull();
            expect(comboBox.get('.selected').text()).toBe('Choose your option');
        });

        it('Test change allowed values and then a value', async function () {
            setDeepProp(comboBox, 'config.values', ['val1', 'val2', 'hello', 'another option']);
            comboBox.setProps({value: 'val2'});

            await vueTicks();

            expect(comboBox.vm.value).toBe('val2');
            expect(comboBox.get('.selected').text()).toBe('val2');
        });
    });

    describe('Test errors', function () {
        it('Test set external empty value when required', async function () {
            setDeepProp(comboBox, 'config.required', true);
            await vueTicks();

            comboBox.setProps({value: ''});

            await vueTicks();

            expect(comboBox.currentError).toBe('required');
        });

        it('Test unselect combobox when required', async function () {
            setDeepProp(comboBox, 'config.required', true);
            await vueTicks();

            comboBox.get('select').setValue('');

            await vueTicks();

            expect(comboBox.currentError).toBe('required');
        });

        it('Test set external value after empty', async function () {
            setDeepProp(comboBox, 'config.required', true);
            comboBox.setProps({value: ''});
            await vueTicks();

            comboBox.setProps({value: 'Value A'});
            await vueTicks();

            expect(comboBox.currentError).toBe('');
        });
    });

    function getSearchElement() {
        return getDropdownElement().childNodes[0]
    }

    function getDropdownElement() {
        return comboBox.get('.dropdown-content').element;
    }

    describe('Test search', function () {
        async function makeSearchable() {
            const values = Array(20).fill(0).map((v, i) => 'Value ' + i);
            setDeepProp(comboBox, 'config.values', values);
            await vueTicks();

            comboBox.vm.comboboxWrapper.dropdown.options.inDuration = 1;
            comboBox.vm.comboboxWrapper.dropdown.options.outDuration = 1;

            return values;
        }

        function assertVisible(element, visible) {
            const displayStyle = window.getComputedStyle(element).display;

            if (visible) {
                expect(displayStyle).not.toBe('none');
            } else {
                expect(displayStyle).toBe('none');
            }
        }

        function assertVisibleItems(combobox, expectedVisible) {
            const [header, ...listItems] = combobox.findAll('li').wrappers;

            expect(header.classes()).not.toContain('search-hidden');

            for (const listItem of listItems) {
                const text = listItem.text();

                const shouldBeVisible = contains(expectedVisible, text);
                if (shouldBeVisible) {
                    expect(listItem.classes()).not.toContain('search-hidden');
                } else {
                    expect(listItem.classes()).toContain('search-hidden');
                }
            }
        }

        it('Test show search field', async function () {
            const values = await makeSearchable();

            assertListElements(values, true);
        });

        it('Test focus search field on open', async function () {
            await makeSearchable();

            await openDropdown();

            const searchInput = comboBox.get('.dropdown-content input');
            expect(document.activeElement).toBe(searchInput.element);
        });

        it('Test keep open on search click', async function () {
            await makeSearchable();

            await openDropdown();

            const searchInput = comboBox.get('.dropdown-content input');
            searchInput.trigger('click');

            await timeout(50);

            assertVisible(getDropdownElement(), true);
        });

        it('Test close on item click', async function () {
            await makeSearchable();

            await openDropdown();

            const firstItem = getDropdownElement().childNodes[1];
            triggerSingleClick(firstItem);

            await timeout(50);

            assertVisible(getDropdownElement(), false);
        });

        it('Test filter on search', async function () {
            await makeSearchable();

            await openDropdown();

            const searchInput = comboBox.get('.dropdown-content input');
            searchInput.setValue('2');

            await vueTicks();

            assertVisibleItems(comboBox, ['Value 2', 'Value 12']);
        });

        it('Test filter on search second input', async function () {
            await makeSearchable();

            await openDropdown();

            const searchInput = comboBox.get('.dropdown-content input');

            searchInput.setValue('2');
            await vueTicks();

            searchInput.setValue('12');
            await vueTicks();

            assertVisibleItems(comboBox, ['Value 12']);
        });

        it('Test filter on search clear input', async function () {
            const values = await makeSearchable();

            await openDropdown();

            const searchInput = comboBox.get('.dropdown-content input');

            searchInput.setValue('2');
            await vueTicks();

            searchInput.setValue('');
            await vueTicks();

            assertVisibleItems(comboBox, values);
        });
    });
});
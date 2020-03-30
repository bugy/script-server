'use strict';

import {mount} from '@vue/test-utils';
import {assert, config as chaiConfig} from 'chai';
import {contains, hasClass, isEmptyString, setInputValue} from '../js/common';
import Combobox from '../js/components/combobox'
import {setDeepProp, timeout, triggerSingleClick, vueTicks, wrapVModel} from './test_utils';

chaiConfig.truncateThreshold = 0;

describe('Test ComboBox', function () {

    before(function () {

    });
    beforeEach(function () {
        this.comboBox = mount(Combobox, {
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
        wrapVModel(this.comboBox);
    });

    afterEach(async function () {
        await vueTicks();
        this.comboBox.destroy();
    });

    after(function () {
    });

    function assertListElements(combobox, expectedTexts) {
        const listChildren = $(combobox.element).find('li');
        assert.equal(expectedTexts.length, listChildren.length - 1);

        for (let i = 0; i < expectedTexts.length; i++) {
            const value = expectedTexts[i];
            assert.equal(value, listChildren.get(i + 1).innerText);
        }
    }

    async function openDropdown(combobox) {
        const triggerInput = $(combobox.element).find('.dropdown-trigger').get(0);

        triggerSingleClick(triggerInput);

        await timeout(50);
    }

    describe('Test config', function () {

        it('Test initial name', function () {
            assert.equal('List param X', this.comboBox.find('select').element.id);
            assert.equal('List param X', this.comboBox.find('label').element.innerText);
        });

        it('Test change name', async function () {
            setDeepProp(this.comboBox, 'config.name', 'testName1');

            await vueTicks();

            assert.equal('testName1', this.comboBox.find('select').element.id);
            assert.equal('testName1', this.comboBox.find('label').element.innerText);
        });

        it('Test initial required', function () {
            assert.equal(false, this.comboBox.find('select').element.required);
        });

        it('Test change required', async function () {
            setDeepProp(this.comboBox, 'config.required', true);

            await vueTicks();

            assert.equal(true, this.comboBox.find('select').element.required);
        });

        it('Test initial description', function () {
            assert.equal('some param', this.comboBox.element.title);
        });

        it('Test change description', async function () {
            setDeepProp(this.comboBox, 'config.description', 'My new desc');

            await vueTicks();

            assert.equal('My new desc', this.comboBox.element.title);
        });

        it('Test initial multiselect', function () {
            assert.notExists(this.comboBox.find('select').attributes('multiple'));

            const listElement = $(this.comboBox.element).find('ul').get(0);
            assert.equal(false, hasClass(listElement, 'multiple-select-dropdown'));
        });


        it('Test initial allowed values', function () {
            const values = ['Value A', 'Value B', 'Value C'];

            const listChildren = $(this.comboBox.element).find('li');

            assert.equal(values.length, listChildren.length - 1);

            assert.equal('Choose your option', listChildren.get(0).innerText);

            for (let i = 0; i < values.length; i++) {
                const value = values[i];
                assert.equal(value, listChildren.get(i + 1).innerText);
            }
        });

        it('Test change allowed values', async function () {
            const values = ['val1', 'val2', 'hello', 'another option'];
            setDeepProp(this.comboBox, 'config.values', values);

            await vueTicks();

            const listChildren = $(this.comboBox.element).find('li');
            assert.equal(values.length, listChildren.length - 1);

            assert.equal('Choose your option', listChildren.get(0).innerText);

            for (let i = 0; i < values.length; i++) {
                const value = values[i];
                assert.equal(value, listChildren.get(i + 1).innerText);
            }
        });
    });

    describe('Test values', function () {

        it('Test initial value', async function () {
            await vueTicks();

            assert.equal(this.comboBox.vm.value, 'Value B');

            const selectedOption = $(this.comboBox.element).find('.selected').text();
            assert.equal(selectedOption, 'Value B');
        });

        it('Test external value change', async function () {
            this.comboBox.setProps({value: 'Value C'});

            await vueTicks();

            assert.equal(this.comboBox.vm.value, 'Value C');

            const selectedOption = $(this.comboBox.element).find('.selected').text();
            assert.equal(selectedOption, 'Value C');
        });

        it('Test select another value', async function () {
            const selectElement = $(this.comboBox.element).find('select');
            selectElement.val('Value A');
            selectElement.trigger('change');

            await vueTicks();

            assert.equal(this.comboBox.vm.value, 'Value A');

            const selectedOption = $(this.comboBox.element).find('.selected').text();
            assert.equal(selectedOption, 'Value A');
        });

        it('Test set unknown value', async function () {
            this.comboBox.setProps({value: 'Xyz'});

            await vueTicks();

            assert.isTrue(isEmptyString(this.comboBox.vm.value));
            assert.equal(1, $(this.comboBox.element).find(':selected').length);
        });

        it('Test set unknown value', async function () {
            this.comboBox.setProps({value: 'Xyz'});

            await vueTicks();

            assert.isTrue(isEmptyString(this.comboBox.vm.value));
            assert.equal('Choose your option', $(this.comboBox.element).find('.selected').text());
        });

        it('Test set multiselect single value', async function () {
            setDeepProp(this.comboBox, 'config.multiselect', true);
            await vueTicks();

            this.comboBox.setProps({value: 'Value A'});

            await vueTicks();
            assert.equal(['Value A'], this.comboBox.vm.value);
            assert.equal('Value A', $(this.comboBox.element).find('.selected').text());
        });

        it('Test set multiselect multiple values', async function () {
            setDeepProp(this.comboBox, 'config.multiselect', true);
            await vueTicks();

            this.comboBox.setProps({value: ['Value A', 'Value C']});

            await vueTicks();
            assert.deepEqual(['Value A', 'Value C'], this.comboBox.vm.value);
            let selectedElements = $(this.comboBox.element).find(':selected');
            assert.equal(2, selectedElements.length);
            assert.equal('Value A', selectedElements.get(0).textContent);
            assert.equal('Value C', selectedElements.get(1).textContent);
        });

        it('Test set multiselect single unknown value', async function () {
            setDeepProp(this.comboBox, 'config.multiselect', true);
            await vueTicks();

            this.comboBox.setProps({value: ['Value X']});

            await vueTicks();
            assert.deepEqual([], this.comboBox.vm.value);
            assert.equal('Choose your option', $(this.comboBox.element).find('.selected').text());
        });

        it('Test set multiselect unknown value from multiple', async function () {
            setDeepProp(this.comboBox, 'config.multiselect', true);
            await vueTicks();

            this.comboBox.setProps({value: ['Value A', 'Value X']});

            await vueTicks();
            assert.deepEqual(['Value A'], this.comboBox.vm.value);
            assert.equal('Value A', $(this.comboBox.element).find('.selected').text());
        });

        it('Test select multiple values in multiselect', async function () {
            setDeepProp(this.comboBox, 'config.multiselect', true);
            await vueTicks();

            const values = ['Value A', 'Value C'];
            const selectElement = $(this.comboBox.element).find('select');
            selectElement.val(values);
            selectElement.trigger('change');

            await vueTicks();

            assert.deepEqual(values, this.comboBox.vm.value);
            let selectedElements = $(this.comboBox.element).find(':selected');
            assert.equal(2, selectedElements.length);
            assert.equal('Value A', selectedElements.get(0).textContent);
            assert.equal('Value C', selectedElements.get(1).textContent);
        });

        it('Test change allowed values with matching value', async function () {
            setDeepProp(this.comboBox, 'config.values', ['val1', 'val2', 'hello', 'Value B', 'another option']);

            await vueTicks();

            assert.equal('Value B', this.comboBox.vm.value);
            assert.equal('Value B', $(this.comboBox.element).find('.selected').text());
        });

        it('Test change allowed values with unmatching value', async function () {
            setDeepProp(this.comboBox, 'config.values', ['val1', 'val2', 'hello', 'another option']);

            await vueTicks();

            assert.isTrue(isEmptyString(this.comboBox.vm.value));
            assert.equal('Choose your option', $(this.comboBox.element).find('.selected').text());
        });

        it('Test change allowed values and then a value', async function () {
            setDeepProp(this.comboBox, 'config.values', ['val1', 'val2', 'hello', 'another option']);
            this.comboBox.setProps({value: 'val2'});

            await vueTicks();

            assert.equal('val2', this.comboBox.vm.value);
            assert.equal('val2', $(this.comboBox.element).find('.selected').text());
        });
    });

    describe('Test errors', function () {
        it('Test set external empty value when required', async function () {
            setDeepProp(this.comboBox, 'config.required', true);
            await vueTicks();

            this.comboBox.setProps({value: ''});

            await vueTicks();

            assert.equal('required', this.comboBox.currentError);
        });

        it('Test unselect combobox when required', async function () {
            setDeepProp(this.comboBox, 'config.required', true);
            await vueTicks();

            const selectElement = $(this.comboBox.element).find('select');
            selectElement.val('');
            selectElement.trigger('change');

            await vueTicks();

            assert.equal('required', this.comboBox.currentError);
        });

        it('Test set external value after empty', async function () {
            setDeepProp(this.comboBox, 'config.required', true);
            this.comboBox.setProps({value: ''});
            await vueTicks();

            this.comboBox.setProps({value: 'Value A'});
            await vueTicks();

            assert.equal('', this.comboBox.currentError);
        });
    });

    function getSearchElement(comboBox) {
        return getDropdownElement(comboBox).childNodes[0]
    }

    function getDropdownElement(combobox) {
        return $(combobox.element).find('.dropdown-content').get(0);
    }

    describe('Test search', function () {
        async function makeSearchable(combobox) {
            const values = Array(20).fill(0).map((v, i) => 'Value ' + i);
            setDeepProp(combobox, 'config.values', values);
            await vueTicks();

            combobox.vm.comboboxWrapper.dropdown.options.inDuration = 1;
            combobox.vm.comboboxWrapper.dropdown.options.outDuration = 1;

            return values;
        }

        function assertVisible(element, visible, message) {
            const displayStyle = window.getComputedStyle(element).display;

            if (visible) {
                assert.notEqual(displayStyle, 'none', message);
            } else {
                assert.equal(displayStyle, 'none', message);
            }
        }

        function assertVisibleItems(combobox, expectedVisible) {
            const [header, ...listItems] = $(combobox.element).find('li').toArray();

            const headerVisible = !hasClass(header, 'search-hidden');
            assert.isTrue(headerVisible);

            for (const listItem of listItems) {
                const text = listItem.innerText;

                const shouldBeVisible = contains(expectedVisible, text);
                const visible = !hasClass(listItem, 'search-hidden');
                assert.equal(visible, shouldBeVisible, 'Item "' + text + '" has wrong visibility');
            }
        }

        it('Test show search field', async function () {
            const values = await makeSearchable(this.comboBox);

            const searchText = $(this.comboBox.element).find('.dropdown-content li').get(0).innerText.trim();
            assert.equal('Search', searchText);
            assertListElements(this.comboBox, values);
        });

        it('Test focus search field on open', async function () {
            await makeSearchable(this.comboBox);

            await openDropdown(this.comboBox);

            const searchInput = $(getSearchElement(this.comboBox)).find('input').get(0);
            assert.equal(searchInput, document.activeElement);
        });

        it('Test keep open on search click', async function () {
            await makeSearchable(this.comboBox);

            await openDropdown(this.comboBox);

            const searchInput = $(getSearchElement(this.comboBox)).find('input').get(0);
            triggerSingleClick(searchInput);

            await timeout(50);

            assertVisible(getDropdownElement(this.comboBox), true);
        });

        it('Test close on item click', async function () {
            await makeSearchable(this.comboBox);

            await openDropdown(this.comboBox);

            const firstItem = getDropdownElement(this.comboBox).childNodes[1];
            triggerSingleClick(firstItem);

            await timeout(50);

            assertVisible(getDropdownElement(this.comboBox), false);
        });

        it('Test filter on search', async function () {
            await makeSearchable(this.comboBox);

            await openDropdown(this.comboBox);

            const inputField = $(getSearchElement(this.comboBox)).find('input').get(0);
            setInputValue(inputField, '2', true);

            await vueTicks();

            assertVisibleItems(this.comboBox, ['Value 2', 'Value 12']);
        });

        it('Test filter on search second input', async function () {
            await makeSearchable(this.comboBox);

            await openDropdown(this.comboBox);

            const inputField = $(getSearchElement(this.comboBox)).find('input').get(0);

            setInputValue(inputField, '2', true);
            await vueTicks();

            setInputValue(inputField, '12', true);
            await vueTicks();

            assertVisibleItems(this.comboBox, ['Value 12']);
        });

        it('Test filter on search clear input', async function () {
            const values = await makeSearchable(this.comboBox);

            await openDropdown(this.comboBox);

            const inputField = $(getSearchElement(this.comboBox)).find('input').get(0);

            setInputValue(inputField, '2', true);
            await vueTicks();

            setInputValue(inputField, '', true);
            await vueTicks();

            assertVisibleItems(this.comboBox, values);
        });
    });
});
'use strict';

import {mount} from 'vue-test-utils';
import {hasClass, isEmptyString} from '../js/common';
import Combobox from '../js/components/combobox'
import {vueTicks, wrapVModel} from './test_utils';

var assert = chai.assert;
chai.config.truncateThreshold = 0;

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

    describe('Test config', function () {

        it('Test initial name', function () {
            assert.equal('List param X', this.comboBox.find('select').element.id);
            assert.equal('List param X', this.comboBox.find('label').element.innerText);
        });

        it('Test change name', async function () {
            this.comboBox.vm.config.name = 'testName1';

            await vueTicks();

            assert.equal('testName1', this.comboBox.find('select').element.id);
            assert.equal('testName1', this.comboBox.find('label').element.innerText);
        });

        it('Test initial required', function () {
            assert.equal(false, this.comboBox.find('select').element.required);
        });

        it('Test change required', async function () {
            this.comboBox.vm.config.required = true;

            await vueTicks();

            assert.equal(true, this.comboBox.find('select').element.required);
        });

        it('Test initial description', function () {
            assert.equal('some param', this.comboBox.element.title);
        });

        it('Test change description', async function () {
            this.comboBox.vm.config.description = 'My new desc';

            await vueTicks();

            assert.equal('My new desc', this.comboBox.element.title);
        });

        it('Test initial multiselect', function () {
            assert.notExists(this.comboBox.find('select').attributes().multiple);

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
            this.comboBox.vm.config.values = values;

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
            this.comboBox.vm.value = 'Value C';

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
            this.comboBox.vm.value = 'Xyz';

            await vueTicks();

            assert.isTrue(isEmptyString(this.comboBox.vm.value));
            assert.equal(1, $(this.comboBox.element).find(':selected').length);
        });

        it('Test set unknown value', async function () {
            this.comboBox.vm.value = 'Xyz';

            await vueTicks();

            assert.isTrue(isEmptyString(this.comboBox.vm.value));
            assert.equal('Choose your option', $(this.comboBox.element).find('.selected').text());
        });

        it('Test set multiselect single value', async function () {
            this.comboBox.vm.config.multiselect = true;
            await vueTicks();

            this.comboBox.vm.value = 'Value A';

            await vueTicks();
            assert.equal(['Value A'], this.comboBox.vm.value);
            assert.equal('Value A', $(this.comboBox.element).find('.selected').text());
        });

        it('Test set multiselect multiple values', async function () {
            this.comboBox.vm.config.multiselect = true;
            await vueTicks();

            this.comboBox.vm.value = ['Value A', 'Value C'];

            await vueTicks();
            assert.deepEqual(['Value A', 'Value C'], this.comboBox.vm.value);
            let selectedElements = $(this.comboBox.element).find(':selected');
            assert.equal(2, selectedElements.length);
            assert.equal('Value A', selectedElements.get(0).textContent);
            assert.equal('Value C', selectedElements.get(1).textContent);
        });

        it('Test set multiselect single unknown value', async function () {
            this.comboBox.vm.config.multiselect = true;
            await vueTicks();

            this.comboBox.vm.value = ['Value X'];

            await vueTicks();
            assert.deepEqual([], this.comboBox.vm.value);
            assert.equal('Choose your option', $(this.comboBox.element).find('.selected').text());
        });

        it('Test set multiselect unknown value from multiple', async function () {
            this.comboBox.vm.config.multiselect = true;
            await vueTicks();

            this.comboBox.vm.value = ['Value A', 'Value X'];

            await vueTicks();
            assert.deepEqual(['Value A'], this.comboBox.vm.value);
            assert.equal('Value A', $(this.comboBox.element).find('.selected').text());
        });

        it('Test select multiple values in multiselect', async function () {
            this.comboBox.vm.config.multiselect = true;
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
            this.comboBox.vm.config.values = ['val1', 'val2', 'hello', 'Value B', 'another option'];

            await vueTicks();

            assert.equal('Value B', this.comboBox.vm.value);
            assert.equal('Value B', $(this.comboBox.element).find('.selected').text());
        });

        it('Test change allowed values with unmatching value', async function () {
            this.comboBox.vm.config.values = ['val1', 'val2', 'hello', 'another option'];

            await vueTicks();

            assert.isTrue(isEmptyString(this.comboBox.vm.value));
            assert.equal('Choose your option', $(this.comboBox.element).find('.selected').text());
        });

        it('Test change allowed values and then a value', async function () {
            this.comboBox.vm.config.values = ['val1', 'val2', 'hello', 'another option'];
            this.comboBox.vm.value = 'val2';

            await vueTicks();

            assert.equal('val2', this.comboBox.vm.value);
            assert.equal('val2', $(this.comboBox.element).find('.selected').text());
        });
    });

    describe('Test errors', function () {
        it('Test set external empty value when required', async function () {
            this.comboBox.vm.config.required = true;
            await vueTicks();

            this.comboBox.vm.value = '';

            await vueTicks();

            assert.equal('required', this.comboBox.currentError);
        });

        it('Test unselect combobox when required', async function () {
            this.comboBox.vm.config.required = true;
            await vueTicks();

            const selectElement = $(this.comboBox.element).find('select');
            selectElement.val('');
            selectElement.trigger('change');

            await vueTicks();

            assert.equal('required', this.comboBox.currentError);
        });

        it('Test set external value after empty', async function () {
            this.comboBox.vm.config.required = true;
            this.comboBox.vm.value = '';
            await vueTicks();

            this.comboBox.vm.value = 'Value A';
            await vueTicks();

            assert.equal('', this.comboBox.currentError);
        });
    });
});
'use strict';

var assert = chai.assert;
chai.config.truncateThreshold = 0;

describe('Test ComboBox', function () {

    before(function () {

    });
    beforeEach(function () {
        this.comboBox = createVue('combobox', {
            config: {
                required: false,
                name: 'List param X',
                description: 'some param',
                values: ['Value A', 'Value B', 'Value C'],
                multiselect: false
            },
            value: 'Value B'
        });
        this.element = this.comboBox.$el;

        this.currentError = null;
        this.comboBox.$on('error', function (value) {
            this.currentError = value
        }.bind(this));
    });

    afterEach(async function () {
        await vueTicks();
        this.comboBox.$destroy();
    });

    after(function () {
    });

    describe('Test config', function () {

        it('Test initial name', function () {
            assert.equal('List param X', $(this.element).find('select').get(0).id);
            assert.equal('List param X', $(this.element).find('label').get(0).innerText);
        });

        it('Test change name', async function () {
            this.comboBox.config.name = 'testName1';

            await vueTicks();

            assert.equal('testName1', $(this.element).find('select').get(0).id);
            assert.equal('testName1', $(this.element).find('label').get(0).innerText);
        });

        it('Test initial required', function () {
            assert.equal(false, $(this.element).find('select').get(0).required);
        });

        it('Test change required', async function () {
            this.comboBox.config.required = true;

            await vueTicks();

            assert.equal(true, $(this.element).find('select').get(0).required);
        });

        it('Test initial description', function () {
            assert.equal('some param', this.element.title);
        });

        it('Test change description', async function () {
            this.comboBox.config.description = 'My new desc';

            await vueTicks();

            assert.equal('My new desc', this.element.title);
        });

        it('Test initial multiselect', function () {
            assert.notExists($(this.element).find('select').attr('multiple'));

            const listElement = $(this.element).find('ul').get(0);
            assert.equal(false, hasClass(listElement, 'multiple-select-dropdown'));
        });


        it('Test initial allowed values', function () {
            const values = ['Value A', 'Value B', 'Value C'];

            const listChildren = $(this.element).find('li');

            assert.equal(values.length, listChildren.length - 1);

            assert.equal('Choose your option', listChildren.get(0).innerText);

            for (let i = 0; i < values.length; i++) {
                const value = values[i];
                assert.equal(value, listChildren.get(i + 1).innerText);
            }
        });

        it('Test change allowed values', async function () {
            const values = ['val1', 'val2', 'hello', 'another option'];
            this.comboBox.config.values = values;

            await vueTicks();

            const listChildren = $(this.element).find('li');
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

            assert.equal(this.comboBox.value, 'Value B');

            const selectedOption = $(this.element).find(":selected").text();
            assert.equal(selectedOption, 'Value B');
        });

        it('Test external value change', async function () {
            this.comboBox.value = 'Value C';

            await vueTicks();

            assert.equal(this.comboBox.value, 'Value C');

            const selectedOption = $(this.element).find(":selected").text();
            assert.equal(selectedOption, 'Value C');
        });

        it('Test select another value', async function () {
            const selectElement = $(this.element).find('select');
            selectElement.val('Value A');
            selectElement.trigger('change');

            await vueTicks();

            assert.equal(this.comboBox.value, 'Value A');

            const selectedOption = $(this.element).find(":selected").text();
            assert.equal(selectedOption, 'Value A');
        });

        it('Test set unknown value', async function () {
            this.comboBox.value = 'Xyz';

            await vueTicks();

            assert.isTrue(isEmptyString(this.comboBox.value));
            assert.equal(1, $(this.element).find(":selected").size());
        });

        it('Test set unknown value', async function () {
            this.comboBox.value = 'Xyz';

            await vueTicks();

            assert.isTrue(isEmptyString(this.comboBox.value));
            assert.equal('Choose your option', $(this.element).find(":selected").text());
        });

        it('Test set multiselect single value', async function () {
            this.comboBox.config.multiselect = true;
            await vueTicks();

            this.comboBox.value = 'Value A';

            await vueTicks();
            assert.equal(['Value A'], this.comboBox.value);
            assert.equal('Value A', $(this.element).find(":selected").text());
        });

        it('Test set multiselect multiple values', async function () {
            this.comboBox.config.multiselect = true;
            await vueTicks();

            this.comboBox.value = ['Value A', 'Value C'];

            await vueTicks();
            assert.deepEqual(['Value A', 'Value C'], this.comboBox.value);
            let selectedElements = $(this.element).find(":selected");
            assert.equal(2, selectedElements.size());
            assert.equal('Value A', selectedElements.get(0).textContent);
            assert.equal('Value C', selectedElements.get(1).textContent);
        });

        it('Test set multiselect single unknown value', async function () {
            this.comboBox.config.multiselect = true;
            await vueTicks();

            this.comboBox.value = ['Value X'];

            await vueTicks();
            assert.deepEqual([], this.comboBox.value);
            assert.equal('Choose your option', $(this.element).find(":selected").text());
        });

        it('Test set multiselect unknown value from multiple', async function () {
            this.comboBox.config.multiselect = true;
            await vueTicks();

            this.comboBox.value = ['Value A', 'Value X'];

            await vueTicks();
            assert.deepEqual(['Value A'], this.comboBox.value);
            assert.equal('Value A', $(this.element).find(":selected").text());
        });

        it('Test select multiple values in multiselect', async function () {
            this.comboBox.config.multiselect = true;
            await vueTicks();

            const values = ['Value A', 'Value C'];
            const selectElement = $(this.element).find('select');
            selectElement.val(values);
            selectElement.trigger('change');

            await vueTicks();

            assert.deepEqual(values, this.comboBox.value);
            let selectedElements = $(this.element).find(":selected");
            assert.equal(2, selectedElements.size());
            assert.equal('Value A', selectedElements.get(0).textContent);
            assert.equal('Value C', selectedElements.get(1).textContent);
        });

        it('Test change allowed values with matching value', async function () {
            this.comboBox.config.values = ['val1', 'val2', 'hello', 'Value B', 'another option'];

            await vueTicks();

            assert.equal('Value B', this.comboBox.value);
            assert.equal('Value B', $(this.element).find(":selected").text());
        });

        it('Test change allowed values with unmatching value', async function () {
            this.comboBox.config.values = ['val1', 'val2', 'hello', 'another option'];

            await vueTicks();

            assert.isTrue(isEmptyString(this.comboBox.value));
            assert.equal('Choose your option', $(this.element).find(":selected").text());
        });

        it('Test change allowed values and then a value', async function () {
            this.comboBox.config.values = ['val1', 'val2', 'hello', 'another option'];
            this.comboBox.value = 'val2';

            await vueTicks();

            assert.equal('val2', this.comboBox.value);
            assert.equal('val2', $(this.element).find(":selected").text());
        });
    });

    describe('Test errors', function () {
        it('Test set external empty value when required', async function () {
            this.comboBox.config.required = true;
            await vueTicks();

            this.comboBox.value = '';

            await vueTicks();

            assert.equal('required', this.currentError);
        });

        it('Test unselect combobox when required', async function () {
            this.comboBox.config.required = true;
            await vueTicks();

            const selectElement = $(this.element).find('select');
            selectElement.val('');
            selectElement.trigger('change');

            await vueTicks();

            assert.equal('required', this.currentError);
        });

        it('Test set external value after empty', async function () {
            this.comboBox.config.required = true;
            this.comboBox.value = '';
            await vueTicks();

            this.comboBox.value = 'Value A';
            await vueTicks();

            assert.equal('', this.currentError);
        });
    });
});
'use strict';

var assert = chai.assert;
chai.config.truncateThreshold = 0;

describe('Test TextField', function () {

    before(function () {

    });
    beforeEach(function () {
        this.textfield = createVue('textfield', {
            config: {
                required: false,
                name: 'Text paparam',
                description: 'this field is used for nothing',
                values: ['Value A', 'Value B', 'Value C'],
                multiselect: false
            },
            value: 'Hello world'
        });
        this.element = this.textfield.$el;

        this.currentError = null;
        this.textfield.$on('error', function (value) {
            this.currentError = value
        }.bind(this));
    });

    afterEach(async function () {
        await vueTicks();
        this.textfield.$destroy();
    });

    after(function () {
    });

    describe('Test config', function () {

        it('Test initial name', function () {
            assert.equal('Text paparam', $(this.element).find('label').text());
        });

        it('Test change name', async function () {
            this.textfield.config.name = 'testName1';

            await vueTicks();

            assert.equal('testName1', $(this.element).find('label').text());
        });

        it('Test initial required', function () {
            assert.equal(false, $(this.element).find('input').get(0).required);
        });

        it('Test change required', async function () {
            this.textfield.config.required = true;

            await vueTicks();

            assert.equal(true, $(this.element).find('input').get(0).required);
        });

        it('Test initial field type', function () {
            assert.equal('text', $(this.element).find('input').attr('type'));
        });

        it('Test change field type to number', async function () {
            Vue.set(this.textfield.config, 'type', 'int');

            await vueTicks();

            assert.equal('number', $(this.element).find('input').attr('type'));
        });

        it('Test change field type to password', async function () {
            Vue.set(this.textfield.config, 'secure', true);

            await vueTicks();

            assert.equal('password', $(this.element).find('input').attr('type'));
        });
    });

    describe('Test values', function () {

        it('Test initial value', async function () {
            await vueTicks();

            assert.equal(this.textfield.value, 'Hello world');
            assert.equal('Hello world', $(this.element).find('input').val());
        });

        it('Test external value change', async function () {
            this.textfield.value = 'XYZ';

            await vueTicks();

            assert.equal(this.textfield.value, 'XYZ');
            assert.equal('XYZ', $(this.element).find('input').val());
        });

        it('Test change value by user', async function () {
            const inputField = $(this.element).find('input');
            setInputValue(inputField, 'abc def', true);

            await vueTicks();

            assert.equal(this.textfield.value, 'abc def');
            assert.equal('abc def', inputField.val());
        });

        it('Test empty value on init', async function () {
            let textfield;
            try {
                textfield = createVue('textfield', {
                    config: {
                        name: 'Text param',
                    },
                    value: ''
                });
                assert.equal(textfield.value, '');
            } finally {
                if (textfield) {
                    await vueTicks();
                    textfield.$destroy();
                }
            }
        });
    });

    describe('Test validaton', function () {
        it('Test set external empty value when required', async function () {
            this.textfield.config.required = true;
            this.textfield.value = '';

            await vueTicks();

            assert.equal('required', this.currentError);
        });

        it('Test user set empty value when required', async function () {
            this.textfield.config.required = true;
            await vueTicks();

            const inputField = $(this.element).find('input');
            setInputValue(inputField, '', true);

            await vueTicks();

            assert.equal('required', this.currentError);
        });

        it('Test set external value after empty when required', async function () {
            this.textfield.config.required = true;
            this.textfield.value = '';
            await vueTicks();

            this.textfield.value = 'A';

            await vueTicks();

            assert.equal('', this.currentError);
        });

        it('Test user set value after empty when required', async function () {
            this.textfield.config.required = true;
            this.textfield.value = '';
            await vueTicks();
            const inputField = $(this.element).find('input');

            setInputValue(inputField, 'A', true);

            await vueTicks();

            assert.equal('', this.currentError);
        });

        it('Test set invalid external value when integer', async function () {
            this.textfield.config.type = 'int';
            this.textfield.value = '1.5';
            await vueTicks();

            assert.equal('integer expected', this.currentError);
        });
    });
});
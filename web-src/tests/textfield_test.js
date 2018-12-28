'use strict';

import {mount} from '@vue/test-utils';
import {assert, config as chaiConfig} from 'chai';
import {setInputValue} from '../js/common';
import Textfield from '../js/components/textfield'
import {mergeDeepProps, setDeepProp, vueTicks, wrapVModel} from './test_utils';

chaiConfig.truncateThreshold = 0;

describe('Test TextField', function () {

    before(function () {

    });
    beforeEach(function () {
        const textfield = mount(Textfield, {
            propsData: {
                config: {
                    required: false,
                    name: 'Text paparam',
                    description: 'this field is used for nothing',
                    values: ['Value A', 'Value B', 'Value C'],
                    multiselect: false
                },
                value: 'Hello world'
            }
        });
        wrapVModel(textfield);

        this.textfield = textfield;
    });

    afterEach(async function () {
        await vueTicks();
        this.textfield.destroy();
    });

    after(function () {
    });

    describe('Test config', function () {

        it('Test initial name', function () {
            assert.equal('Text paparam', this.textfield.find('label').text());
        });

        it('Test change name', async function () {
            setDeepProp(this.textfield, 'config.name', 'testName1');

            await vueTicks();

            assert.equal('testName1', this.textfield.find('label').text());
        });

        it('Test initial required', function () {
            assert.equal(false, this.textfield.find('input').element.required);
        });

        it('Test change required', async function () {
            setDeepProp(this.textfield, 'config.required', true);

            await vueTicks();

            assert.equal(true, this.textfield.find('input').element.required);
        });

        it('Test initial field type', function () {
            assert.equal('text', this.textfield.find('input').element.type);
        });

        it('Test change field type to number', async function () {
            setDeepProp(this.textfield, 'config.type', 'int');

            await vueTicks();

            assert.equal('number', this.textfield.find('input').element.type);
        });

        it('Test change field type to password', async function () {
            setDeepProp(this.textfield, 'config.secure', true);

            await vueTicks();

            assert.equal('password', this.textfield.find('input').element.type);
        });
    });

    describe('Test values', function () {

        it('Test initial value', async function () {
            await vueTicks();

            assert.equal(this.textfield.vm.value, 'Hello world');
            assert.equal('Hello world', this.textfield.find('input').element.value);
        });

        it('Test external value change', async function () {
            this.textfield.setProps({value: 'XYZ'});

            await vueTicks();

            assert.equal(this.textfield.vm.value, 'XYZ');
            assert.equal('XYZ', this.textfield.find('input').element.value);
        });

        it('Test change value by user', async function () {
            const inputField = this.textfield.find('input').element;
            setInputValue(inputField, 'abc def', true);

            await vueTicks();

            assert.equal(this.textfield.vm.value, 'abc def');
            assert.equal('abc def', inputField.value);
        });

        it('Test empty value on init', async function () {
            let textfield;
            try {
                textfield = mount(Textfield, {
                    propsData: {
                        config: {
                            name: 'Text param'
                        },
                        value: ''
                    }
                });
                assert.equal(textfield.vm.value, '');
            } finally {
                if (textfield) {
                    await vueTicks();
                    textfield.destroy();
                }
            }
        });
    });

    describe('Test validaton', function () {
        it('Test set external empty value when required', async function () {
            setDeepProp(this.textfield, 'config.required', true);
            this.textfield.setProps({value: ''});

            await vueTicks();

            assert.equal('required', this.textfield.currentError);
        });

        it('Test user set empty value when required', async function () {
            setDeepProp(this.textfield, 'config.required', true);
            await vueTicks();

            const inputField = this.textfield.find('input').element;
            setInputValue(inputField, '', true);

            await vueTicks();

            assert.equal('required', this.textfield.currentError);
        });

        it('Test set external value after empty when required', async function () {
            setDeepProp(this.textfield, 'config.required', true);
            this.textfield.setProps({value: ''});
            await vueTicks();

            this.textfield.setProps({value: 'A'});

            await vueTicks();

            assert.equal('', this.textfield.currentError);
        });

        it('Test user set value after empty when required', async function () {
            setDeepProp(this.textfield, 'config.required', true);
            this.textfield.setProps({value: ''});
            await vueTicks();
            const inputField = this.textfield.find('input').element;


            setInputValue(inputField, 'A', true);

            await vueTicks();

            assert.equal('', this.textfield.currentError);
        });

        it('Test set invalid external value when integer', async function () {
            setDeepProp(this.textfield, 'config.type', 'int');
            this.textfield.setProps({value: '1.5'});
            await vueTicks();

            assert.equal('integer expected', this.textfield.currentError);
        });
    });
});
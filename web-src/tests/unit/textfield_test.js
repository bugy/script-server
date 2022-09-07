'use strict';

import Textfield from '@/common/components/textfield'
import {isEmptyString, setInputValue} from '@/common/utils/common';
import {mount} from '@vue/test-utils';
import {attachToDocument, mapArrayWrapper, setDeepProp, timeout, vueTicks, wrapVModel} from './test_utils';

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

    describe('Test config', function () {

        it('Test initial name', function () {
            expect(this.textfield.find('label').text()).toEqual('Text paparam')
        });

        it('Test change name', async function () {
            setDeepProp(this.textfield, 'config.name', 'testName1');

            await vueTicks();

            expect(this.textfield.find('label').text()).toEqual('testName1')
        });

        it('Test initial required', function () {
            expect(this.textfield.find('input').element.required).toEqual(false)
        });

        it('Test change required', async function () {
            setDeepProp(this.textfield, 'config.required', true);

            await vueTicks();

            expect(this.textfield.find('input').element.required).toEqual(true)
        });

        it('Test initial field type', function () {
            expect(this.textfield.find('input').element.type).toEqual('text')
        });

        it('Test change field type to number', async function () {
            setDeepProp(this.textfield, 'config.type', 'int');

            await vueTicks();

            expect(this.textfield.find('input').element.type).toEqual('number')
        });

        it('Test change field type to password', async function () {
            setDeepProp(this.textfield, 'config.secure', true);

            await vueTicks();

            expect(this.textfield.find('input').element.type).toEqual('password')
        });
    });

    describe('Test values', function () {

        it('Test initial value', async function () {
            await vueTicks();

            expect(this.textfield.vm.value).toBe('Hello world')
            expect(this.textfield.find('input').element.value).toBe('Hello world')
        });

        it('Test external value change', async function () {
            this.textfield.setProps({value: 'XYZ'});

            await vueTicks();

            expect(this.textfield.vm.value).toBe('XYZ')
            expect(this.textfield.find('input').element.value).toBe('XYZ')
        });

        it('Test change value by user', async function () {
            const inputField = this.textfield.find('input').element;
            setInputValue(inputField, 'abc def', true);

            await vueTicks();

            expect(this.textfield.vm.value).toBe('abc def')
            expect(inputField.value).toBe('abc def')
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
                expect(textfield.vm.value).toBe('')
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

            expect(this.textfield.currentError).toBe('required')
        });

        it('Test user set empty value when required', async function () {
            setDeepProp(this.textfield, 'config.required', true);
            await vueTicks();

            const inputField = this.textfield.find('input').element;
            setInputValue(inputField, '', true);

            await vueTicks();

            expect(this.textfield.currentError).toBe('required')
        });

        it('Test set external value after empty when required', async function () {
            setDeepProp(this.textfield, 'config.required', true);
            this.textfield.setProps({value: ''});
            await vueTicks();

            this.textfield.setProps({value: 'A'});

            await vueTicks();

            expect(this.textfield.currentError).toBe('')
        });

        it('Test user set value after empty when required', async function () {
            setDeepProp(this.textfield, 'config.required', true);
            this.textfield.setProps({value: ''});
            await vueTicks();
            const inputField = this.textfield.find('input').element;


            setInputValue(inputField, 'A', true);

            await vueTicks();

            expect(this.textfield.currentError).toBe('')
        });

        it('Test set invalid external value when integer', async function () {
            setDeepProp(this.textfield, 'config.type', 'int');
            this.textfield.setProps({value: '1.5'});
            await vueTicks();

            expect(this.textfield.currentError).toBe('integer expected')
        });
    });

    describe('Test IP validaton', function () {

        async function testValidation(textfield, type, value, expectedError) {
            setDeepProp(textfield, 'config.type', type);
            textfield.setProps({value: value});
            await vueTicks();

            if (isEmptyString(expectedError)) {
                expect(textfield.currentError).toBe(expectedError)
            } else {
                expect(textfield.currentError).toInclude(expectedError)
            }
        }

        it('Test IPv4 127.0.0.1', async function () {
            await testValidation(this.textfield, 'ip4', '127.0.0.1', '')
        });

        it('Test IPv4 255.255.255.255', async function () {
            await testValidation(this.textfield, 'ip4', '255.255.255.255', '')
        });

        it('Test IPv4 valid with trim', async function () {
            await testValidation(this.textfield, 'ip4', '  192.168.0.1\n', '')
        });

        it('Test IPv4 invalid block count', async function () {
            await testValidation(this.textfield, 'ip4', '127.0.1', 'IPv4 expected')
        });

        it('Test IPv4 empty block', async function () {
            await testValidation(this.textfield, 'ip4', '127..0.1', 'Empty IP block')
        });

        it('Test IPv4 invalid block', async function () {
            await testValidation(this.textfield, 'ip4', '127.wrong.0.1', 'Invalid block wrong')
        });

        it('Test IPv4 large number', async function () {
            await testValidation(this.textfield, 'ip4', '192.168.256.0', 'Out of range')
        });

        it('Test IPv6 ::', async function () {
            await testValidation(this.textfield, 'ip6', '::', '')
        });

        it('Test IPv6 ::0', async function () {
            await testValidation(this.textfield, 'ip6', '::0', '')
        });

        it('Test IPv6 ABCD::0', async function () {
            await testValidation(this.textfield, 'ip6', 'ABCD::0', '')
        });

        it('Test IPv6 ABCD::192.168.2.12', async function () {
            await testValidation(this.textfield, 'ip6', 'ABCD::192.168.2.12', '')
        });

        it('Test IPv6 ABCD:0123::4567:192.168.2.12', async function () {
            await testValidation(this.textfield, 'ip6', 'ABCD:0123::4567:192.168.2.12', '')
        });

        it('Test IPv6 valid with trim', async function () {
            await testValidation(this.textfield, 'ip6', '  ABCD::0123  ', '')
        });

        it('Test IPv6 valid with different cases', async function () {
            await testValidation(this.textfield, 'ip6', 'AbCd::123:dEf', '')
        });

        it('Test IPv6 valid blocks count', async function () {
            await testValidation(this.textfield, 'ip6', '1:2:3:4:5:6:7:8', '')
        });

        it('Test IPv6 valid blocks count with ip4', async function () {
            await testValidation(this.textfield, 'ip6', '1:2:3:4:5:6:127.0.0.1', '')
        });

        it('Test IPv6 too much blocks', async function () {
            await testValidation(this.textfield, 'ip6', '1:2:3:4:5:6:7:8:9', 'Should be 8 blocks')
        });

        it('Test IPv6 too much blocks with zero compression', async function () {
            await testValidation(this.textfield, 'ip6', '1:2:3::4:5:6:7:8:9', 'Should be 8 blocks')
        });

        it('Test IPv6 too little blocks', async function () {
            await testValidation(this.textfield, 'ip6', '1:2:3:4:5:6:7', 'Should be 8 blocks')
        });

        it('Test IPv6 double ::', async function () {
            await testValidation(this.textfield, 'ip6', '1::2::3', 'allowed only once')
        });

        it('Test IPv6 invalid long block', async function () {
            await testValidation(this.textfield, 'ip6', '1::ABCDE:3', 'Invalid block ABCDE')
        });

        it('Test IPv6 invalid character', async function () {
            await testValidation(this.textfield, 'ip6', '1::ABCG:3', 'Invalid block ABCG')
        });

        it('Test IPv6 when ip4 not last', async function () {
            await testValidation(this.textfield, 'ip6', '1::127.0.0.1:AB', 'should be the last')
        });

        it('Test IPv6 when ip4 wrong', async function () {
            await testValidation(this.textfield, 'ip6', '1::127..1', 'Invalid IPv4 block 127..1')
        });

        it('Test IPv6 when ip4 too early', async function () {
            await testValidation(this.textfield, 'ip6', '1:2:3:4:5:127.0.0.1', 'Invalid block 127.0.0.1')
        });

        it('Test Any IP when correct ip4', async function () {
            await testValidation(this.textfield, 'ip', '127.0.0.1', '')
        });

        it('Test Any IP when wrong ip4', async function () {
            await testValidation(this.textfield, 'ip', '127.0..1', 'IPv4 or IPv6 expected')
        });

        it('Test Any IP when correct ip6', async function () {
            await testValidation(this.textfield, 'ip', 'ABCD::0', '')
        });

        it('Test Any IP when wrong ip6', async function () {
            await testValidation(this.textfield, 'ip', 'ABCX::0', 'IPv4 or IPv6 expected')
        });
    });


    describe('Test autocomplete', function () {
        let autocompleteComponent

        beforeEach(async function () {
            autocompleteComponent = mount(Textfield, {
                attachTo: attachToDocument(),
                propsData: {
                    config: {
                        required: true,
                        name: 'Text autocomplete',
                        values: ['Value A', 'Value B', 'Value C'],
                        type: 'editable_list'
                    },
                    value: ''
                }
            });
            wrapVModel(autocompleteComponent);

            await vueTicks()
        });

        async function clickOnInputField() {
            await autocompleteComponent.find('input').trigger('click')
            await timeout(150)
        }

        function getOptionTexts() {
            const listElements = autocompleteComponent.findAll('ul li')
            return mapArrayWrapper(listElements, wrapper => wrapper.text())
        }

        it('Test open dropdown on click', async function () {
            await clickOnInputField()

            expect(autocompleteComponent.find('input').classes()).toContain('autocomplete')

            expect(autocompleteComponent.find('ul').element).toBeVisible()

            const options = getOptionTexts()
            expect(options).toEqual(['Value A', 'Value B', 'Value C'])
        });

        it('Test open dropdown on click when input value matches all elements', async function () {
            await autocompleteComponent.find('input').setValue('alu');

            await clickOnInputField()

            const options = getOptionTexts()
            expect(options).toEqual(['Value A', 'Value B', 'Value C'])

            expect(autocompleteComponent.vm.value).toBe('alu')
        });

        it('Test open dropdown on click when input value matches single element', async function () {
            await autocompleteComponent.find('input').setValue('B');

            await clickOnInputField()

            const options = getOptionTexts()
            expect(options).toEqual(['Value B'])

            expect(autocompleteComponent.vm.value).toBe('B')
        });

        it('Test open dropdown on click when vm value matches single element', async function () {
            await autocompleteComponent.setProps({value: 'B'});

            await clickOnInputField()

            const options = getOptionTexts()
            expect(options).toEqual(['Value B'])

            expect(autocompleteComponent.vm.value).toBe('B')
        });

        it('Test select option from dropdown', async function () {
            await clickOnInputField()

            await autocompleteComponent.findAll('ul li').at(1).trigger('click')
            await timeout(300)

            expect(autocompleteComponent.find('ul').element).not.toBeVisible()
            expect(autocompleteComponent.vm.value).toBe('Value B')
        });

        it('Test update values', async function () {
            setDeepProp(autocompleteComponent, 'config.values', ['Abc', 'Def', 'Xyz']);
            await vueTicks()

            await clickOnInputField()

            const options = getOptionTexts()
            expect(options).toEqual(['Abc', 'Def', 'Xyz'])
        });

    })

});
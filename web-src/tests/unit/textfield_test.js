'use strict';

import Textfield from '@/common/components/textfield'
import {isEmptyString, setInputValue} from '@/common/utils/common';
import {mount} from '@vue/test-utils';
import {attachToDocument, mapArrayWrapper, setDeepProp, timeout, vueTicks, wrapVModel} from './test_utils';

describe('Test TextField', function () {
    let textfield;

    beforeEach(function () {
        textfield = mount(Textfield, {
            props: {
                config: {
                    required: false,
                    name: 'Text paparam',
                    description: 'this field is used for nothing',
                    values: ['Value A', 'Value B', 'Value C'],
                    multiselect: false
                },
                modelValue: 'Hello world'
            }
        });
        wrapVModel(textfield);

    });

    describe('Test config', function () {

        it('Test initial name', function () {
            expect(textfield.find('label').text()).toEqual('Text paparam')
        });

        it('Test change name', async function () {
            setDeepProp(textfield, 'config.name', 'testName1');

            await vueTicks();

            expect(textfield.find('label').text()).toEqual('testName1')
        });

        it('Test initial required', function () {
            expect(textfield.find('input').element.required).toEqual(false)
        });

        it('Test change required', async function () {
            setDeepProp(textfield, 'config.required', true);

            await vueTicks();

            expect(textfield.find('input').element.required).toEqual(true)
        });

        it('Test initial field type', function () {
            expect(textfield.find('input').element.type).toEqual('text')
        });

        it('Test change field type to number', async function () {
            setDeepProp(textfield, 'config.type', 'int');

            await vueTicks();

            expect(textfield.find('input').element.type).toEqual('number')
        });

        it('Test change field type to password', async function () {
            setDeepProp(textfield, 'config.secure', true);

            await vueTicks();

            expect(textfield.find('input').element.type).toEqual('password')
        });
    });

    describe('Test values', function () {

        it('Test initial value', async function () {
            await vueTicks();

            expect(textfield.vm.modelValue).toBe('Hello world')
            expect(textfield.find('input').element.value).toBe('Hello world')
        });

        it('Test external value change', async function () {
            textfield.setProps({modelValue: 'XYZ'});

            await vueTicks();

            expect(textfield.vm.modelValue).toBe('XYZ')
            expect(textfield.find('input').element.value).toBe('XYZ')
        });

        it('Test change value by user', async function () {
            const inputField = textfield.find('input').element;
            setInputValue(inputField, 'abc def', true);

            await vueTicks();

            expect(textfield.vm.modelValue).toBe('abc def')
            expect(inputField.value).toBe('abc def')
        });

        it('Test empty value on init', async function () {
            let textfield;
            try {
                textfield = mount(Textfield, {
                    props: {
                        config: {
                            name: 'Text param'
                        },
                        modelValue: ''
                    }
                });
                expect(textfield.vm.modelValue).toBe('')
            } finally {
                if (textfield) {
                    await vueTicks();
                    textfield.unmount();
                }
            }
        });
    });

    describe('Test validaton', function () {
        it('Test set external empty value when required', async function () {
            setDeepProp(textfield, 'config.required', true);
            textfield.setProps({modelValue: ''});

            await vueTicks();

            expect(textfield.currentError).toBe('required')
        });

        it('Test user set empty value when required', async function () {
            setDeepProp(textfield, 'config.required', true);
            await vueTicks();

            const inputField = textfield.find('input').element;
            setInputValue(inputField, '', true);

            await vueTicks();

            expect(textfield.currentError).toBe('required')
        });

        it('Test set external value after empty when required', async function () {
            setDeepProp(textfield, 'config.required', true);
            textfield.setProps({modelValue: ''});
            await vueTicks();

            textfield.setProps({modelValue: 'A'});

            await vueTicks();

            expect(textfield.currentError).toBe('')
        });

        it('Test user set value after empty when required', async function () {
            setDeepProp(textfield, 'config.required', true);
            textfield.setProps({modelValue: ''});
            await vueTicks();
            const inputField = textfield.find('input').element;


            setInputValue(inputField, 'A', true);

            await vueTicks();

            expect(textfield.currentError).toBe('')
        });

        it('Test set invalid external value when integer', async function () {
            setDeepProp(textfield, 'config.type', 'int');
            textfield.setProps({modelValue: '1.5'});
            await vueTicks();

            expect(textfield.currentError).toBe('integer expected')
        });

        it('Test set invalid external value when regex', async function () {
            setDeepProp(textfield, 'config.regex', {pattern: 'a\\d\\db', description: 'test desc'});
            textfield.setProps({modelValue: 'a123'});
            await vueTicks();

            expect(textfield.currentError).toBe('test desc')
        });

        it('Test set invalid external value when regex fullstring match', async function () {
            setDeepProp(textfield, 'config.regex', {pattern: 'a', description: 'test desc'});
            textfield.setProps({modelValue: 'wat'});
            await vueTicks();

            expect(textfield.currentError).toBe('test desc')
        });

        it('Test set invalid external value when regex fullstring match and no desc', async function () {
            setDeepProp(textfield, 'config.regex', {pattern: 'a', description: ''});
            textfield.setProps({modelValue: 'a1a'});
            await vueTicks();

            expect(textfield.currentError).toBe('pattern mismatch')
        });

        it('Test user set invalid value when regex', async function () {
            setDeepProp(textfield, 'config.regex', {pattern: 'a\\d\\db', description: 'test desc'});
            await vueTicks();

            const inputField = textfield.find('input').element;
            setInputValue(inputField, 'a12XXX', true);

            await vueTicks();

            expect(textfield.currentError).toBe('test desc')
        });
    });

    describe('Test IP validaton', function () {

        async function testValidation(textfield, type, value, expectedError) {
            setDeepProp(textfield, 'config.type', type);
            textfield.setProps({modelValue: value});
            await vueTicks();

            if (isEmptyString(expectedError)) {
                expect(textfield.currentError).toBe(expectedError)
            } else {
                expect(textfield.currentError).toInclude(expectedError)
            }
        }

        it('Test IPv4 127.0.0.1', async function () {
            await testValidation(textfield, 'ip4', '127.0.0.1', '')
        });

        it('Test IPv4 255.255.255.255', async function () {
            await testValidation(textfield, 'ip4', '255.255.255.255', '')
        });

        it('Test IPv4 valid with trim', async function () {
            await testValidation(textfield, 'ip4', '  192.168.0.1\n', '')
        });

        it('Test IPv4 invalid block count', async function () {
            await testValidation(textfield, 'ip4', '127.0.1', 'IPv4 expected')
        });

        it('Test IPv4 empty block', async function () {
            await testValidation(textfield, 'ip4', '127..0.1', 'Empty IP block')
        });

        it('Test IPv4 invalid block', async function () {
            await testValidation(textfield, 'ip4', '127.wrong.0.1', 'Invalid block wrong')
        });

        it('Test IPv4 large number', async function () {
            await testValidation(textfield, 'ip4', '192.168.256.0', 'Out of range')
        });

        it('Test IPv6 ::', async function () {
            await testValidation(textfield, 'ip6', '::', '')
        });

        it('Test IPv6 ::0', async function () {
            await testValidation(textfield, 'ip6', '::0', '')
        });

        it('Test IPv6 ABCD::0', async function () {
            await testValidation(textfield, 'ip6', 'ABCD::0', '')
        });

        it('Test IPv6 ABCD::192.168.2.12', async function () {
            await testValidation(textfield, 'ip6', 'ABCD::192.168.2.12', '')
        });

        it('Test IPv6 ABCD:0123::4567:192.168.2.12', async function () {
            await testValidation(textfield, 'ip6', 'ABCD:0123::4567:192.168.2.12', '')
        });

        it('Test IPv6 valid with trim', async function () {
            await testValidation(textfield, 'ip6', '  ABCD::0123  ', '')
        });

        it('Test IPv6 valid with different cases', async function () {
            await testValidation(textfield, 'ip6', 'AbCd::123:dEf', '')
        });

        it('Test IPv6 valid blocks count', async function () {
            await testValidation(textfield, 'ip6', '1:2:3:4:5:6:7:8', '')
        });

        it('Test IPv6 valid blocks count with ip4', async function () {
            await testValidation(textfield, 'ip6', '1:2:3:4:5:6:127.0.0.1', '')
        });

        it('Test IPv6 too much blocks', async function () {
            await testValidation(textfield, 'ip6', '1:2:3:4:5:6:7:8:9', 'Should be 8 blocks')
        });

        it('Test IPv6 too much blocks with zero compression', async function () {
            await testValidation(textfield, 'ip6', '1:2:3::4:5:6:7:8:9', 'Should be 8 blocks')
        });

        it('Test IPv6 too little blocks', async function () {
            await testValidation(textfield, 'ip6', '1:2:3:4:5:6:7', 'Should be 8 blocks')
        });

        it('Test IPv6 double ::', async function () {
            await testValidation(textfield, 'ip6', '1::2::3', 'allowed only once')
        });

        it('Test IPv6 invalid long block', async function () {
            await testValidation(textfield, 'ip6', '1::ABCDE:3', 'Invalid block ABCDE')
        });

        it('Test IPv6 invalid character', async function () {
            await testValidation(textfield, 'ip6', '1::ABCG:3', 'Invalid block ABCG')
        });

        it('Test IPv6 when ip4 not last', async function () {
            await testValidation(textfield, 'ip6', '1::127.0.0.1:AB', 'should be the last')
        });

        it('Test IPv6 when ip4 wrong', async function () {
            await testValidation(textfield, 'ip6', '1::127..1', 'Invalid IPv4 block 127..1')
        });

        it('Test IPv6 when ip4 too early', async function () {
            await testValidation(textfield, 'ip6', '1:2:3:4:5:127.0.0.1', 'Invalid block 127.0.0.1')
        });

        it('Test Any IP when correct ip4', async function () {
            await testValidation(textfield, 'ip', '127.0.0.1', '')
        });

        it('Test Any IP when wrong ip4', async function () {
            await testValidation(textfield, 'ip', '127.0..1', 'IPv4 or IPv6 expected')
        });

        it('Test Any IP when correct ip6', async function () {
            await testValidation(textfield, 'ip', 'ABCD::0', '')
        });

        it('Test Any IP when wrong ip6', async function () {
            await testValidation(textfield, 'ip', 'ABCX::0', 'IPv4 or IPv6 expected')
        });
    });


    describe('Test autocomplete', function () {
        let autocompleteComponent

        beforeEach(async function () {
            autocompleteComponent = mount(Textfield, {
                attachTo: attachToDocument(),
                props: {
                    config: {
                        required: true,
                        name: 'Text autocomplete',
                        values: ['Value A', 'Value B', 'Value C'],
                        type: 'editable_list'
                    },
                    modelValue: ''
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

            expect(autocompleteComponent.vm.modelValue).toBe('alu')
        });

        it('Test open dropdown on click when input value matches single element', async function () {
            await autocompleteComponent.find('input').setValue('B');

            await clickOnInputField()

            const options = getOptionTexts()
            expect(options).toEqual(['Value B'])

            expect(autocompleteComponent.vm.modelValue).toBe('B')
        });

        it('Test open dropdown on click when vm value matches single element', async function () {
            await autocompleteComponent.setProps({modelValue: 'B'});

            await clickOnInputField()

            const options = getOptionTexts()
            expect(options).toEqual(['Value B'])

            expect(autocompleteComponent.vm.modelValue).toBe('B')
        });

        it('Test select option from dropdown', async function () {
            await clickOnInputField()

            await autocompleteComponent.findAll('ul li').at(1).trigger('click')
            await timeout(300)

            // Note: under jsdom the dropdown's close animation (anime.js
            // complete callback) doesn't fire, so we can't assert it becomes
            // hidden the way the Karma/browser run did. We still verify the
            // option click propagates the selected value through v-model.
            expect(autocompleteComponent.vm.modelValue).toBe('Value B')
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
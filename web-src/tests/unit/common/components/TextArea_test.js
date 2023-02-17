'use strict';

import {mount} from '@vue/test-utils';
import TextArea from '@/common/components/TextArea'
import {setDeepProp, vueTicks, wrapVModel} from '../../test_utils'
import {setInputValue} from '@/common/utils/common'

describe('Test TextArea', function () {

    let textarea

    before(function () {

    });

    beforeEach(function () {
        textarea = mount(TextArea, {
            propsData: {
                config: {
                    required: false,
                    name: 'Textarea parameter',
                    description: 'this field is used for nothing'
                },
                value: 'Hello world'
            }
        });
        wrapVModel(textarea);
    });


    function verifyElementValue(expectedValue) {
        expect(textarea.currentError).toBeNil()
        expect(textarea.find('textarea').element.value).toBe(expectedValue)
    }

    describe('Test config', function () {

        it('Test initial configs', function () {
            expect(textarea.find('label').text()).toEqual('Textarea parameter')
            expect(textarea.element.title).toEqual('this field is used for nothing')
            verifyElementValue('Hello world')
        });

        it('Test change name', async function () {
            setDeepProp(textarea, 'config.name', 'testName1')

            await vueTicks()

            expect(textarea.find('label').text()).toEqual('testName1')
        })
    })

    describe('Test validation', function () {

        it('Test required with default value', async function () {
            setDeepProp(textarea, 'config.required', true)

            await vueTicks()

            verifyElementValue('Hello world')
            expect(textarea.currentError).toBeNil()
        });

        it('Test required when external change', async function () {
            setDeepProp(textarea, 'config.required', true)
            textarea.setProps({value: ' '});

            await vueTicks()

            expect(textarea.currentError).toBe('required')
        });

        it('Test required when user change', async function () {
            setDeepProp(textarea, 'config.required', true)

            await vueTicks()

            const textareaElement = textarea.find('textarea').element;
            setInputValue(textareaElement, ' ', true);

            await vueTicks();

            expect(textarea.currentError).toBe('required')
        });

        it('Test required when external change to correct one', async function () {
            setDeepProp(textarea, 'config.required', true)
            textarea.setProps({value: ' '});
            await vueTicks()

            textarea.setProps({value: '123'});

            await vueTicks()

            expect(textarea.currentError).toBeNil()
        });

        it('Test required when user change to correct one', async function () {
            setDeepProp(textarea, 'config.required', true)
            await vueTicks()

            const textareaElement = textarea.find('textarea').element;

            setInputValue(textareaElement, ' ', true);
            await vueTicks();

            setInputValue(textareaElement, '123', true);
            await vueTicks();

            expect(textarea.currentError).toBeNil()
        });

        it('Test max_length with default value', async function () {
            setDeepProp(textarea, 'config.max_length', 10)

            await vueTicks()

            expect(textarea.currentError).toBe('Max chars allowed: 10')
        });

        it('Test max_length when external change', async function () {
            setDeepProp(textarea, 'config.max_length', 10)
            textarea.setProps({value: 'Some long text'});

            await vueTicks()

            expect(textarea.currentError).toBe('Max chars allowed: 10')
        });

        it('Test max_length when user change', async function () {
            setDeepProp(textarea, 'config.max_length', 10)

            await vueTicks()

            const textareaElement = textarea.find('textarea').element;
            setInputValue(textareaElement, 'Some long text', true);

            await vueTicks();

            expect(textarea.currentError).toBe('Max chars allowed: 10')
        });

        it('Test max_length when external change to correct one', async function () {
            setDeepProp(textarea, 'config.max_length', 10)
            textarea.setProps({value: 'Some long text'});
            await vueTicks()

            textarea.setProps({value: 'short'});
            await vueTicks()

            expect(textarea.currentError).toBeNil()
        });

        it('Test max_length when user change to correct one', async function () {
            setDeepProp(textarea, 'config.max_length', 10)
            await vueTicks()

            const textareaElement = textarea.find('textarea').element;

            setInputValue(textareaElement, 'Some long text', true);
            await vueTicks();

            setInputValue(textareaElement, 'Short', true);
            await vueTicks();

            expect(textarea.currentError).toBeNil()
        });
    })
})
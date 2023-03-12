'use strict'

import {mount} from '@vue/test-utils'
import {attachToDocument, focus, getNodeText, mapArrayWrapper, vueTicks, wrapVModel} from '../../test_utils'
import ChipsList from '@/common/components/ChipsList'


describe('Test ChipList', function () {
    let chipList

    beforeEach(async function () {
        chipList = mount(ChipsList, {
            attachTo: attachToDocument(),
            propsData: {
                value: ['abc', 'def'],
            }
        })
        chipList.vm.$parent.$forceUpdate()
        wrapVModel(chipList)

        await vueTicks()
    })

    afterEach(async function () {
        await vueTicks()
        chipList.destroy()
    })

    describe('Test setting value', function () {

        it('Test initial value', function () {
            verifyChips(['abc', 'def'])
        })
    })

    describe('Test comma-separated input', function () {

        async function setInput(inputValue) {
            const input = getInput()
            input.element.focus()
            await input.setValue(inputValue)
            await vueTicks()
        }

        it('Test write input value without comma', async function () {
            await setInput('xyz')

            verifyChips(['abc', 'def'])
            verifyInputValue('xyz')
            expect(getInput().element).toHaveFocus()
        })

        it('Test write input value with comma', async function () {
            await setInput('xyz,')

            verifyChips(['abc', 'def', 'xyz'])
            verifyInputValue('')
            expect(getInput().element).toHaveFocus()
        })

        it('Test write input value with escaped comma', async function () {
            await setInput('xyz\\,')

            verifyChips(['abc', 'def'])
            verifyInputValue('xyz\\,')
            expect(getInput().element).toHaveFocus()
        })

        it('Test write input value with multiple commas', async function () {
            await setInput('xyz,hello , world\\,!,end')

            verifyChips(['abc', 'def', 'xyz', 'hello', 'world,!'])
            verifyInputValue('end')
            expect(getInput().element).toHaveFocus()
        })

        it('Test write input value without comma with focus loss', async function () {
            await setInput('xyz')
            focus(chipList.find('.chip').element)
            await vueTicks()

            verifyChips(['abc', 'def', 'xyz'])
            verifyInputValue('')
            expect(getInput().element).not.toHaveFocus()
        })

        it('Test write input value with escaped comma with focus loss', async function () {
            await setInput('xyz\\,hello')
            focus(chipList.find('.chip').element)
            await vueTicks()

            verifyChips(['abc', 'def', 'xyz,hello'])
            verifyInputValue('')
            expect(getInput().element).not.toHaveFocus()
        })
    })

    function verifyChips(expectedValue) {
        const chips = mapArrayWrapper(chipList.findAll('.chip'), wrapper => getNodeText(wrapper.element))
        expect(chips).toEqual(expectedValue)
    }

    function verifyInputValue(expectedValue) {
        const input = getInput()
        expect(input.element.value).toBe(expectedValue)
    }

    function getInput() {
        return chipList.get('.chips input')
    }

})
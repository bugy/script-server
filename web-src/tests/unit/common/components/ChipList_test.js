'use strict'

import {mount} from '@vue/test-utils'
import {attachToDocument, vueTicks, wrapVModel} from '../../test_utils'
import ChipsList from '@/common/components/ChipsList'

// Vuetify migration: chips are v-chip elements inside the v-combobox field;
// the text input is the combobox's own input (search model).

describe('Test ChipList', function () {
    let chipList

    beforeEach(async function () {
        chipList = mount(ChipsList, {
            attachTo: attachToDocument(),
            props: {
                modelValue: ['abc', 'def'],
            }
        })
        wrapVModel(chipList)

        await vueTicks()
    })

    afterEach(async function () {
        await vueTicks()
        chipList.unmount()
    })

    describe('Test setting value', function () {

        it('Test initial value', function () {
            verifyChips(['abc', 'def'])
        })

        it('Test external value change', async function () {
            await chipList.setProps({modelValue: ['xyz']})

            verifyChips(['xyz'])
        })
    })

    describe('Test comma-separated input', function () {

        async function setInput(inputValue) {
            const input = getInput()
            input.element.focus()
            await input.trigger('focus')
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
            await getInput().trigger('blur')
            await vueTicks()

            verifyChips(['abc', 'def', 'xyz'])
            verifyInputValue('')
        })

        it('Test write input value with escaped comma with focus loss', async function () {
            await setInput('xyz\\,hello')
            await getInput().trigger('blur')
            await vueTicks()

            verifyChips(['abc', 'def', 'xyz,hello'])
            verifyInputValue('')
        })
    })

    describe('Test chip removal', function () {

        it('Test remove chip via close button', async function () {
            chipList.get('.v-chip .v-chip__close').trigger('click')
            await vueTicks()

            verifyChips(['def'])
        })
    })

    function chipText(chipElement) {
        // exclude the close button (its md icon ligature is plain text in jsdom)
        const copy = chipElement.cloneNode(true)
        copy.querySelectorAll('.v-chip__close').forEach(el => el.remove())
        return copy.textContent.trim()
    }

    function verifyChips(expectedValue) {
        const chips = chipList.findAll('.v-chip').map(wrapper => chipText(wrapper.element))
        expect(chips).toEqual(expectedValue)
    }

    function verifyInputValue(expectedValue) {
        const input = getInput()
        expect(input.element.value).toBe(expectedValue)
    }

    function getInput() {
        return chipList.get('.chips-list input')
    }

})

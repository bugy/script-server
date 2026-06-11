'use strict';

import {mount} from '@vue/test-utils';
import RadioGroup from '@/common/components/RadioGroup'
import {vueTicks} from '../../test_utils'

describe('Test RadioGroup', function () {

    let radioGroup

    const options = [
        {value: 'path', text: 'Path on server'},
        {value: 'code', text: 'Edit script code', icon: 'warning', iconTitle: 'unsaved changes'},
        {value: 'upload', text: 'Upload script'}
    ]

    beforeEach(function () {
        radioGroup = mount(RadioGroup, {
            props: {
                modelValue: 'path',
                groupName: 'test-group',
                options
            }
        });
    });

    it('Test render options', function () {
        const labels = radioGroup.findAll('.v-radio .v-label span')
        expect(labels.map(l => l.text())).toEqual(['Path on server', 'Edit script code', 'Upload script'])

        const radios = radioGroup.findAll('input[type=radio]')
        expect(radios.length).toBe(3)
        expect(radios.map(r => r.element.name)).toEqual(['test-group', 'test-group', 'test-group'])
    });

    it('Test initial selection', function () {
        const radios = radioGroup.findAll('input[type=radio]')
        expect(radios.map(r => r.element.checked)).toEqual([true, false, false])
        expect(radioGroup.findAll('.v-radio').at(0).classes()).toContain('active')
    });

    it('Test external selection change', async function () {
        await radioGroup.setProps({modelValue: 'upload'})

        const radios = radioGroup.findAll('input[type=radio]')
        expect(radios.map(r => r.element.checked)).toEqual([false, false, true])
        expect(radioGroup.findAll('.v-radio').at(2).classes()).toContain('active')
    });

    it('Test user selection emits update:modelValue', async function () {
        await radioGroup.findAll('input[type=radio]').at(1).setValue(true)
        await vueTicks()

        const emitted = radioGroup.emitted('update:modelValue')
        expect(emitted.at(-1)).toEqual(['code'])
    });

    it('Test option icon', function () {
        const icons = radioGroup.findAll('.v-radio i.option-icon')
        expect(icons.length).toBe(1)
        expect(icons.at(0).text()).toBe('warning')
        expect(icons.at(0).element.title).toBe('unsaved changes')
    });
})

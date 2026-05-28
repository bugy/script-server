'use strict';

import {mount} from '@vue/test-utils';
import DateField from '@/common/components/inputs/DateField';
import {setDeepProp, vueTicks, wrapVModel} from '../../../test_utils';

describe('Test DateField', function () {

    let datefield;

    beforeEach(async function () {
        datefield = mount(DateField, {
            propsData: {
                config: {
                    name: 'Start date',
                    required: false,
                    description: 'Pick a start date'
                },
                value: '2025-05-27'
            }
        });
        wrapVModel(datefield);
        await vueTicks();
    });

    describe('Test config', function () {

        it('Test label displays config.name', function () {
            expect(datefield.find('label').text()).toBe('Start date');
        });

        it('Test input type is date', function () {
            expect(datefield.find('input').element.type).toBe('date');
        });

        it('Test input is not required by default', function () {
            expect(datefield.find('input').element.required).toBe(false);
        });

        it('Test input becomes required when config.required is set', async function () {
            setDeepProp(datefield, 'config.required', true);
            await vueTicks();

            expect(datefield.find('input').element.required).toBe(true);
        });

        it('Test input is enabled by default', function () {
            expect(datefield.find('input').element.disabled).toBe(false);
        });

        it('Test input is disabled when disabled prop is true', async function () {
            datefield.setProps({disabled: true});
            await vueTicks();

            expect(datefield.find('input').element.disabled).toBe(true);
        });

        it('Test label has active class when value is set', function () {
            expect(datefield.find('label').classes()).toContain('active');
        });

        it('Test label has no active class when value is empty', async function () {
            datefield.setProps({value: ''});
            await vueTicks();

            expect(datefield.find('label').classes()).not.toContain('active');
        });

    });

    describe('Test values', function () {

        it('Test displays initial value', function () {
            expect(datefield.find('input').element.value).toBe('2025-05-27');
            expect(datefield.vm.value).toBe('2025-05-27');
        });

        it('Test external value change updates input', async function () {
            datefield.setProps({value: '2026-01-01'});
            await vueTicks();

            expect(datefield.find('input').element.value).toBe('2026-01-01');
            expect(datefield.vm.value).toBe('2026-01-01');
        });

        it('Test user change emits input event with new value', async function () {
            const input = datefield.find('input');
            input.element.value = '2026-06-15';
            await input.trigger('change');
            await vueTicks();

            expect(datefield.vm.value).toBe('2026-06-15');
        });

        it('Test user change to another valid date', async function () {
            const input = datefield.find('input');
            input.element.value = '2025-12-31';
            await input.trigger('change');
            await vueTicks();

            expect(datefield.vm.value).toBe('2025-12-31');
        });

    });

    describe('Test validation', function () {

        it('Test no error for valid initial value', function () {
            expect(datefield.vm.error).toBe('');
        });

        it('Test no error when not required and value becomes empty', async function () {
            datefield.setProps({value: ''});
            await vueTicks();

            expect(datefield.currentError).toBe('');
        });

        it('Test required error when required and value is empty string', async function () {
            setDeepProp(datefield, 'config.required', true);
            datefield.setProps({value: ''});
            await vueTicks();

            expect(datefield.currentError).toBe('required');
        });

        it('Test required error when required and value is null', async function () {
            setDeepProp(datefield, 'config.required', true);
            datefield.setProps({value: null});
            await vueTicks();

            expect(datefield.currentError).toBe('required');
        });

        it('Test no error when required and value is present', async function () {
            setDeepProp(datefield, 'config.required', true);
            datefield.setProps({value: '2025-09-01'});
            await vueTicks();

            expect(datefield.currentError).toBe('');
        });

        it('Test error clears when value provided after being empty', async function () {
            setDeepProp(datefield, 'config.required', true);
            datefield.setProps({value: ''});
            await vueTicks();
            expect(datefield.currentError).toBe('required');

            datefield.setProps({value: '2025-12-01'});
            await vueTicks();
            expect(datefield.currentError).toBe('');
        });

        it('Test no error when disabled even if required and empty', async function () {
            datefield.setProps({disabled: true});
            setDeepProp(datefield, 'config.required', true);
            datefield.setProps({value: ''});
            await vueTicks();

            expect(datefield.currentError).toBe('');
        });

        it('Test data-error attribute reflects current error', async function () {
            setDeepProp(datefield, 'config.required', true);
            datefield.setProps({value: ''});
            await vueTicks();

            expect(datefield.find('div').attributes('data-error')).toBe('required');
        });

        it('Test data-error attribute is empty when no error', async function () {
            datefield.setProps({value: '2025-05-27'});
            await vueTicks();

            expect(datefield.find('div').attributes('data-error')).toBe('');
        });

    });

});

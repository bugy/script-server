'use strict';

import {mount} from '@vue/test-utils';
import TimeField from '@/common/components/inputs/TimeField';
import {setDeepProp, vueTicks, wrapVModel} from '../../../test_utils';

describe('Test TimeField', function () {

    let timefield;

    beforeEach(async function () {
        timefield = mount(TimeField, {
            propsData: {
                config: {
                    name: 'Start time',
                    required: false,
                    description: 'Pick a start time'
                },
                value: '10:00'
            }
        });
        wrapVModel(timefield);
        await vueTicks();
    });

    describe('Test config', function () {

        it('Test label displays config.name', function () {
            expect(timefield.find('label').text()).toBe('Start time');
        });

        it('Test input type is time', function () {
            expect(timefield.find('input').element.type).toBe('time');
        });

        it('Test input is not required by default', function () {
            expect(timefield.find('input').element.required).toBe(false);
        });

        it('Test input becomes required when config.required is set', async function () {
            setDeepProp(timefield, 'config.required', true);
            await vueTicks();

            expect(timefield.find('input').element.required).toBe(true);
        });

        it('Test input is enabled by default', function () {
            expect(timefield.find('input').element.disabled).toBe(false);
        });

        it('Test input is disabled when disabled prop is true', async function () {
            timefield.setProps({disabled: true});
            await vueTicks();

            expect(timefield.find('input').element.disabled).toBe(true);
        });

        it('Test label has active class when value is set', function () {
            expect(timefield.find('label').classes()).toContain('active');
        });

        it('Test label has no active class when value is empty', async function () {
            timefield.setProps({value: ''});
            await vueTicks();

            expect(timefield.find('label').classes()).not.toContain('active');
        });

    });

    describe('Test values', function () {

        it('Test displays initial value', function () {
            expect(timefield.find('input').element.value).toBe('10:00');
            expect(timefield.vm.value).toBe('10:00');
        });

        it('Test external value change updates input', async function () {
            timefield.setProps({value: '14:30'});
            await vueTicks();

            expect(timefield.find('input').element.value).toBe('14:30');
            expect(timefield.vm.value).toBe('14:30');
        });

        it('Test user change emits input event with new value', async function () {
            const input = timefield.find('input');
            input.element.value = '08:15';
            await input.trigger('change');
            await vueTicks();

            expect(timefield.vm.value).toBe('08:15');
        });

        it('Test user change to another valid time', async function () {
            const input = timefield.find('input');
            input.element.value = '23:59';
            await input.trigger('change');
            await vueTicks();

            expect(timefield.vm.value).toBe('23:59');
        });

    });

    describe('Test validation', function () {

        it('Test no error for valid initial value', function () {
            expect(timefield.vm.error).toBe('');
        });

        it('Test no error when not required and value becomes empty', async function () {
            timefield.setProps({value: ''});
            await vueTicks();

            expect(timefield.currentError).toBe('');
        });

        it('Test required error when required and value is empty string', async function () {
            setDeepProp(timefield, 'config.required', true);
            timefield.setProps({value: ''});
            await vueTicks();

            expect(timefield.currentError).toBe('required');
        });

        it('Test required error when required and value is null', async function () {
            setDeepProp(timefield, 'config.required', true);
            timefield.setProps({value: null});
            await vueTicks();

            expect(timefield.currentError).toBe('required');
        });

        it('Test no error when required and value is present', async function () {
            setDeepProp(timefield, 'config.required', true);
            timefield.setProps({value: '09:00'});
            await vueTicks();

            expect(timefield.currentError).toBe('');
        });

        it('Test error clears when value provided after being empty', async function () {
            setDeepProp(timefield, 'config.required', true);
            timefield.setProps({value: ''});
            await vueTicks();
            expect(timefield.currentError).toBe('required');

            timefield.setProps({value: '12:00'});
            await vueTicks();
            expect(timefield.currentError).toBe('');
        });

        it('Test no error when disabled even if required and empty', async function () {
            timefield.setProps({disabled: true});
            setDeepProp(timefield, 'config.required', true);
            timefield.setProps({value: ''});
            await vueTicks();

            expect(timefield.currentError).toBe('');
        });

        it('Test data-error attribute reflects current error', async function () {
            setDeepProp(timefield, 'config.required', true);
            timefield.setProps({value: ''});
            await vueTicks();

            expect(timefield.find('div').attributes('data-error')).toBe('required');
        });

        it('Test data-error attribute is empty when no error', async function () {
            await vueTicks();
            timefield.setProps({value: '10:00'});
            await vueTicks();

            expect(timefield.find('div').attributes('data-error')).toBe('');
        });

    });

});

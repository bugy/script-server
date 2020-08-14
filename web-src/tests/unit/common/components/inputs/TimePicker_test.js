'use strict';

import {mount} from '@vue/test-utils';
import TimePicker from "@/common/components/inputs/TimePicker";
import {vueTicks, wrapVModel} from "../../../test_utils";

describe('Test TimePicker', function () {
    let timepicker;

    before(function () {

    });
    beforeEach(async function () {
        timepicker = mount(TimePicker, {
            propsData: {
                label: 'Test picker',
                value: '15:30',
                required: true
            }
        });
        timepicker.vm.$parent.$forceUpdate();
        wrapVModel(timepicker);

        await vueTicks();
    });

    afterEach(async function () {
        await vueTicks();
        timepicker.destroy();
    });

    after(function () {
    });

    describe('Test config', function () {

        it('Test initial props', function () {
            expect(timepicker.find('label').text()).toBe('Test picker')
            expect(timepicker.find('input').element.value).toBe('15:30')
            expect(timepicker.vm.value).toBe('15:30')
            expect(timepicker.vm.error).toBeEmpty()
        });

        it('Test user changes time to 19:30', async function () {
            timepicker.find('input').setValue('19:30');

            await vueTicks();

            expect(timepicker.find('input').element.value).toBe('19:30')
            expect(timepicker.vm.value).toBe('19:30')
            expect(timepicker.vm.error).toBeEmpty()
        });

        it('Test user changes time to 23:59', async function () {
            timepicker.find('input').setValue('23:59');

            await vueTicks();

            expect(timepicker.find('input').element.value).toBe('23:59')
            expect(timepicker.vm.value).toBe('23:59')
            expect(timepicker.vm.error).toBeEmpty()
        });

        it('Test user changes time to 24:00', async function () {
            timepicker.find('input').setValue('24:00');

            await vueTicks();

            expect(timepicker.find('input').element.value).toBe('24:00')
            expect(timepicker.vm.value).toBe('15:30')
            expect(timepicker.vm.error).toBe('Format HH:MM')
            expect(timepicker.currentError).toBe('Format HH:MM')
        });

        it('Test user changes time to 9:45', async function () {
            timepicker.find('input').setValue('9:45');

            await vueTicks();

            expect(timepicker.find('input').element.value).toBe('9:45')
            expect(timepicker.vm.value).toBe('9:45')
            expect(timepicker.vm.error).toBeEmpty()
        });

        it('Test user changes time to 2:10', async function () {
            timepicker.find('input').setValue('2:10');

            await vueTicks();

            expect(timepicker.find('input').element.value).toBe('2:10')
            expect(timepicker.vm.value).toBe('2:10')
            expect(timepicker.vm.error).toBeEmpty()
        });

        it('Test user changes time to 09:10', async function () {
            timepicker.find('input').setValue('09:10');

            await vueTicks();

            expect(timepicker.find('input').element.value).toBe('09:10')
            expect(timepicker.vm.value).toBe('09:10')
            expect(timepicker.vm.error).toBeEmpty()
        });

        it('Test user changes time to 09:60', async function () {
            timepicker.find('input').setValue('09:60');

            await vueTicks();

            expect(timepicker.find('input').element.value).toBe('09:60')
            expect(timepicker.vm.value).toBe('15:30')
            expect(timepicker.vm.error).toBe('Format HH:MM')
            expect(timepicker.currentError).toBe('Format HH:MM')
        });

        it('Test system changes time to 16:01', async function () {
            timepicker.setProps({'value': '16:01'})

            await vueTicks();

            expect(timepicker.find('input').element.value).toBe('16:01')
            expect(timepicker.vm.value).toBe('16:01')
            expect(timepicker.vm.error).toBeEmpty()
        });

        it('Test system changes time to 31:01', async function () {
            timepicker.setProps({'value': '31:01'})

            await vueTicks();

            expect(timepicker.find('input').element.value).toBe('31:01')
            expect(timepicker.vm.value).toBe('31:01')
            expect(timepicker.vm.error).toBe('Format HH:MM')
            expect(timepicker.currentError).toBe('Format HH:MM')
        });

    });
});
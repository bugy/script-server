'use strict';
import Paginator from '@/common/components/history/Paginator';
import {mount} from '@vue/test-utils';
import {createScriptServerTestVue} from '../test_utils';

const localVue = createScriptServerTestVue();

describe('Paginator.vue', function () {
    let wrapper;

    afterEach(function () {
        if (wrapper) {
            wrapper.destroy();
        }
    });

    it('renders empty entries info when total is 0', function () {
        wrapper = mount(Paginator, {
            localVue,
            propsData: {
                page: 1,
                pageSize: 25,
                total: 0,
                totalPages: 1
            }
        });

        expect(wrapper.find('.records-info').text()).toBe('No entries');
        expect(wrapper.find('.page-indicator').text()).toBe('Page 1 of 1');
    });

    it('renders correct records range info text', function () {
        wrapper = mount(Paginator, {
            localVue,
            propsData: {
                page: 2,
                pageSize: 25,
                total: 100,
                totalPages: 4
            }
        });

        expect(wrapper.find('.records-info').text()).toBe('Showing 26 - 50 of 100 entries');
        expect(wrapper.find('.page-indicator').text()).toBe('Page 2 of 4');
    });

    it('disables first and prev buttons on page 1', function () {
        wrapper = mount(Paginator, {
            localVue,
            propsData: {
                page: 1,
                pageSize: 25,
                total: 50,
                totalPages: 2
            }
        });

        const buttons = wrapper.findAll('button');
        const firstBtn = buttons.at(0);
        const prevBtn = buttons.at(1);
        const nextBtn = buttons.at(2);
        const lastBtn = buttons.at(3);

        expect(firstBtn.element.disabled).toBe(true);
        expect(prevBtn.element.disabled).toBe(true);
        expect(nextBtn.element.disabled).toBe(false);
        expect(lastBtn.element.disabled).toBe(false);
    });

    it('disables next and last buttons on last page', function () {
        wrapper = mount(Paginator, {
            localVue,
            propsData: {
                page: 2,
                pageSize: 25,
                total: 50,
                totalPages: 2
            }
        });

        const buttons = wrapper.findAll('button');
        const firstBtn = buttons.at(0);
        const prevBtn = buttons.at(1);
        const nextBtn = buttons.at(2);
        const lastBtn = buttons.at(3);

        expect(firstBtn.element.disabled).toBe(false);
        expect(prevBtn.element.disabled).toBe(false);
        expect(nextBtn.element.disabled).toBe(true);
        expect(lastBtn.element.disabled).toBe(true);
    });

    it('emits page-change event when clicking next', async function () {
        wrapper = mount(Paginator, {
            localVue,
            propsData: {
                page: 1,
                pageSize: 25,
                total: 50,
                totalPages: 2
            }
        });

        const nextBtn = wrapper.findAll('button').at(2);
        await nextBtn.trigger('click');

        expect(wrapper.emitted('page-change')).toBeTruthy();
        expect(wrapper.emitted('page-change')[0]).toEqual([2]);
    });

    it('emits size-change event when selecting new page size', async function () {
        wrapper = mount(Paginator, {
            localVue,
            propsData: {
                page: 1,
                pageSize: 25,
                total: 100,
                totalPages: 4,
                pageSizeOptions: [10, 25, 50, 100]
            }
        });

        const select = wrapper.find('select');
        await select.setValue('50');

        expect(wrapper.emitted('size-change')).toBeTruthy();
        expect(wrapper.emitted('size-change')[0]).toEqual([50]);
    });
});

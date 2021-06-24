'use strict';
import AppHistoryPanel from '@/main-app/components/history/AppHistoryPanel';
import router from '@/main-app/router/router';
import pageModule from '@/main-app/store/page'
import {mount} from '@vue/test-utils';
import VueRouter from 'vue-router';
import Vuex from 'vuex';
import {attachToDocument, createScriptServerTestVue, vueTicks} from '../../../test_utils';

const localVue = createScriptServerTestVue();
localVue.use(Vuex);
localVue.use(VueRouter);

describe('Test AppHistoryPanel', function () {
    let historyPanel;
    let store;

    beforeEach(async function () {
        store = new Vuex.Store({
            modules: {
                history: {
                    namespaced: true,
                    state: {
                        loading: false,
                        detailsLoading: false
                    }
                },
                page: pageModule
            }
        });

        historyPanel = mount(AppHistoryPanel, {
            attachTo: attachToDocument(),
            store,
            localVue,
            router
        });

        await vueTicks();
    });

    afterEach(function () {
        historyPanel.destroy();
    });

    describe('Test loading states', function () {

        it('test nothing loading', async function () {
            expect(store.state.page.pageLoading).toBeFalse();
        });

        it('test loading when history loading', async function () {
            store.state.history.loading = true;

            await vueTicks();

            expect(store.state.page.pageLoading).toBeTrue();
        });

        it('test loading when history loading becomes false', async function () {
            store.state.history.loading = true;

            await vueTicks();

            store.state.history.loading = false;

            await vueTicks();

            expect(store.state.page.pageLoading).toBeFalse();
        });

        it('test loading when history loading when historyDetails route', async function () {
            router.push('/history/123')
            store.state.history.loading = true;

            await vueTicks();

            expect(store.state.page.pageLoading).toBeFalse();
        });

        it('test loading when historyDetails loading', async function () {
            router.push('/history/123')
            store.state.history.detailsLoading = true;

            await vueTicks();

            expect(store.state.page.pageLoading).toBeTrue();
        });

        it('test loading when historyDetails loading becomes false', async function () {
            router.push('/history/123')
            store.state.history.detailsLoading = true;

            await vueTicks();

            store.state.history.detailsLoading = false;

            await vueTicks();

            expect(store.state.page.pageLoading).toBeFalse();
        });

        it('test loading when historyDetails loading when history route', async function () {
            router.push('/history')
            store.state.history.detailsLoading = true;

            await vueTicks();

            expect(store.state.page.pageLoading).toBeFalse();
        });
    })
});

'use strict';
import AppHistoryPanel from '@/main-app/components/history/AppHistoryPanel';
import router from '@/main-app/router/router';
import {axiosInstance} from '@/common/utils/axios_utils';
import {mount} from '@vue/test-utils';
import {createPinia, setActivePinia} from 'pinia';
import {useHistoryStore} from '@/common/stores/history';
import {usePageStore} from '@/main-app/stores/page';
import MockAdapter from 'axios-mock-adapter';
import {attachToDocument, createScriptServerTestVue, vueTicks} from '../../../test_utils';

describe('Test AppHistoryPanel', function () {
    let historyPanel;
    let pinia;
    let historyStore;
    let pageStore;
    let axiosMock;

    beforeEach(async function () {
        // Mock all history API calls so component mounts don't trigger real network requests
        axiosMock = new MockAdapter(axiosInstance);
        axiosMock.onGet(/history\/execution_log/).reply(200, []);

        pinia = createPinia();
        setActivePinia(pinia);

        historyStore = useHistoryStore();
        historyStore.loading = false;
        historyStore.detailsLoading = false;

        pageStore = usePageStore();

        // Start on the history route so ExecutionsLog mounts and init() runs
        await router.push('/history');

        historyPanel = mount(AppHistoryPanel, {
            attachTo: attachToDocument(),
            global: {plugins: [pinia, router]},
        });

        await vueTicks();

        // Reset loading state that may have been set by init() above
        historyStore.loading = false;
        historyStore.detailsLoading = false;
        await vueTicks();
    });

    afterEach(function () {
        historyPanel.unmount();
        axiosMock.restore();
    });

    describe('Test loading states', function () {

        it('test nothing loading', async function () {
            expect(pageStore.pageLoading).toBeFalse();
        });

        it('test loading when history loading', async function () {
            historyStore.loading = true;

            await vueTicks();

            expect(pageStore.pageLoading).toBeTrue();
        });

        it('test loading when history loading becomes false', async function () {
            historyStore.loading = true;

            await vueTicks();

            historyStore.loading = false;

            await vueTicks();

            expect(pageStore.pageLoading).toBeFalse();
        });

        it('test loading when history loading when historyDetails route', async function () {
            await router.push('/history/123')
            await vueTicks();

            // Reset state set by ExecutionDetails mounting
            historyStore.loading = false;
            historyStore.detailsLoading = false;
            await vueTicks();

            historyStore.loading = true;

            await vueTicks();

            expect(pageStore.pageLoading).toBeFalse();
        });

        it('test loading when historyDetails loading', async function () {
            await router.push('/history/123')
            await vueTicks();

            // Reset state set by ExecutionDetails mounting
            historyStore.loading = false;
            historyStore.detailsLoading = false;
            await vueTicks();

            historyStore.detailsLoading = true;

            await vueTicks();

            expect(pageStore.pageLoading).toBeTrue();
        });

        it('test loading when historyDetails loading becomes false', async function () {
            await router.push('/history/123')
            await vueTicks();

            // Reset state set by ExecutionDetails mounting
            historyStore.loading = false;
            historyStore.detailsLoading = false;
            await vueTicks();

            historyStore.detailsLoading = true;

            await vueTicks();

            historyStore.detailsLoading = false;

            await vueTicks();

            expect(pageStore.pageLoading).toBeFalse();
        });

        it('test loading when historyDetails loading when history route', async function () {
            // Already on /history from beforeEach; state already reset
            historyStore.detailsLoading = true;

            await vueTicks();

            expect(pageStore.pageLoading).toBeFalse();
        });
    })
});

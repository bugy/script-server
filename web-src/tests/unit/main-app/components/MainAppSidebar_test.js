'use strict';
import {mount} from '@vue/test-utils';
import {createPinia, setActivePinia} from 'pinia';
import MainAppSidebar from '@/main-app/components/MainAppSidebar';
import {useServerConfigStore} from '@/main-app/stores/serverConfig';
import {attachToDocument, createScriptServerTestVue, vueTicks} from '../../test_utils';
import router from '@/main-app/router/router';

describe('Test MainAppSidebar', function () {
    let sidebar;
    let pinia;

    beforeEach(async function () {
        pinia = createPinia();
        setActivePinia(pinia);

        const serverConfigStore = useServerConfigStore();
        serverConfigStore.serverName = 'Custom name';

        sidebar = mount(MainAppSidebar, {
            attachTo: attachToDocument(),
            global: {plugins: [pinia, router]},
        });
        await sidebar.vm.$nextTick();
    });

    afterEach(function () {
        sidebar.unmount();
    });

    describe('Test title', function () {

        it('test title from config', async function () {
            const header = sidebar.find('.server-header');

            expect(header.text()).toBe('Custom name');
        });

        it('test change title in config', async function () {
            useServerConfigStore().serverName = 'Another name';
            await vueTicks();

            const header = sidebar.find('.server-header');

            expect(header.text()).toBe('Another name');
        });

        it('test default title when missing', async function () {
            useServerConfigStore().serverName = null;
            await vueTicks();

            const header = sidebar.find('.server-header');

            expect(header.text()).toBe('Script server');
        });

        it('test long title', async function () {
            useServerConfigStore().serverName = 'Some very very long title';
            await vueTicks();

            const header = sidebar.find('.server-header');

            expect(header.classes()).toContain('header-gt-21-chars');
        });
    });

});

'use strict';
import {mount} from '@vue/test-utils';
import {createStore as createVuexStore} from 'vuex';
import VueRouter from 'vue-router';
import MainAppSidebar from '@/main-app/components/MainAppSidebar';
import {attachToDocument, createScriptServerTestVue, vueTicks} from '../../test_utils';
import router from '@/main-app/router/router';
describe('Test MainAppSidebar', function () {
    let sidebar;
    let store;

    beforeEach(async function () {
        store = createVuexStore({
            modules: {
                serverConfig: {
                    namespaced: true,
                    state: {
                        serverName: 'Custom name'
                    }
                },
                scripts: {
                    namespaced: true,
                    state: {
                        scripts: []
                    }
                },
            }
        });

        sidebar = mount(MainAppSidebar, {
            attachTo: attachToDocument(),
            global: {plugins: [store, router]},
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
            store.state.serverConfig.serverName = 'Another name';
            await vueTicks();

            const header = sidebar.find('.server-header');

            expect(header.text()).toBe('Another name');
        });

        it('test default title when missing', async function () {
            store.state.serverConfig.serverName = null;
            await vueTicks();

            const header = sidebar.find('.server-header');

            expect(header.text()).toBe('Script server');
        });

        it('test long title', async function () {
            store.state.serverConfig.serverName = 'Some very very long title';
            await vueTicks();

            const header = sidebar.find('.server-header');

            expect(header.classes()).toContain('header-gt-21-chars');
        });
    });

});

'use strict';
import scripts from '@/admin/store/scripts-module'
import {axiosInstance} from '@/common/utils/axios_utils';
import MockAdapter from 'axios-mock-adapter';
import Vuex from 'vuex';
import {createScriptServerTestVue} from '../test_utils'

const localVue = createScriptServerTestVue();
localVue.use(Vuex);

let axiosMock;
const flushPromises = () => new Promise(resolve => setTimeout(resolve));


function mockGetScripts(scripts) {
    axiosMock.onGet('scripts')
        .reply(200, {scripts});
}

describe('Test admin script module', function () {
    let store;

    beforeEach(async function () {
        store = new Vuex.Store({
            modules: {
                scripts: scripts
            }
        });

        axiosMock = new MockAdapter(axiosInstance)
    });

    afterEach(function () {
        axiosMock.restore()
    })

    describe('Test load scripts', function () {

        it('test load single script', async function () {
            mockGetScripts([{'name': 'script1'}]);

            await store.dispatch('scripts/init');
            await flushPromises();

            expect(store.state.scripts.scripts).toEqual(
                [{'name': 'script1', 'parsingFailed': undefined}])
            expect(store.state.scripts.loading).toBeFalse()
        });

        it('test load multiple unsorted scripts', async function () {
            mockGetScripts([
                {'name': 'def', 'group': 'some_group'},
                {'name': 'xyz', 'parsing_failed': false},
                {'name': 'abc', 'parsing_failed': true}]);

            await store.dispatch('scripts/init');
            await flushPromises();

            expect(store.state.scripts.scripts).toEqual([
                {'name': 'abc', 'parsingFailed': true},
                {'name': 'def', 'parsingFailed': undefined},
                {'name': 'xyz', 'parsingFailed': false}
            ])
            expect(store.state.scripts.loading).toBeFalse()
        });
        }
    )
});

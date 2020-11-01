'use strict';

import ScriptConfig from '@/admin/components/scripts-config/ScriptConfig';
import ScriptConfigForm from '@/admin/components/scripts-config/ScriptConfigForm';
import {createLocalVue, mount} from '@vue/test-utils';
import {assert, config as chaiConfig} from 'chai';
import Vuex from 'vuex';
import {vueTicks} from '../test_utils';
import {findField, setValueByUser} from './ParameterConfigForm_test';


chaiConfig.truncateThreshold = 0;

const localVue = createLocalVue();
localVue.use(Vuex);

describe('Test ScriptConfig', function () {
    let store;
    let configComponent;

    beforeEach(async function () {
        store = new Vuex.Store({
            modules: {
                scriptConfig: {
                    namespaced: true,
                    state: {
                        scriptName: 'test_script',
                        scriptConfig: {'name': 'test_script'}
                    },
                    actions: {
                        init({commit, state}, scriptName) {

                        },

                        save({dispatch, state}) {

                        }
                    }
                }
            }
        });

        configComponent = mount(ScriptConfig, {
            store,
            localVue,
            attachToDocument: true,
            propsData: {scriptName: 'script1'}
        });

        await vueTicks();
    });

    afterEach(async function () {
        await vueTicks();

        configComponent.destroy();
    });

    const _findField = (expectedName, failOnMissing = true) => {
        const form = configComponent.find(ScriptConfigForm);
        return findField(form.vm, expectedName, failOnMissing);
    };

    async function _setValueByUser(fieldName, value) {
        const form = configComponent.find(ScriptConfigForm);
        await setValueByUser(form.vm, fieldName, value);
    }

    describe('Test show config', function () {
        it('Test show simple values', async function () {
            store.state.scriptConfig.scriptConfig = {
                'name': 's1',
                'group': 'important',
                'script_path': 'ping',
                'description': 'some desc',
                'working_directory': '/home',
                'requires_terminal': true,
                'include': 'script.json',
                'bash_formatting': false
            };

            await vueTicks();

            assert.equal('s1', _findField('Script name').value);
            assert.equal('important', _findField('Group').value);
            assert.equal('ping', _findField('Script path').value);
            assert.equal('some desc', _findField('Description').value);
            assert.equal('/home', _findField('Working directory').value);
            assert.equal(true, _findField('Requires terminal').value);
            assert.equal('script.json', _findField('Include config').value);
            assert.equal(false, _findField('Bash formatting').value);
        });
    });

    describe('Test edit config', function () {
        it('Test edit group', async function () {
            await _setValueByUser('Group', 'xyz');

            assert.equal('xyz', store.state.scriptConfig.scriptConfig.group);
        });
    });

    describe('Test edit allowed_users', function () {
        it('Test edit allowed_users manually', async function () {
            await _setValueByUser('Allow all', false);
            await _setValueByUser('Allowed users', ['user A', 'user B']);

            expect(store.state.scriptConfig.scriptConfig.allowed_users).toEqual(['user A', 'user B'])
        });
    });

    describe('Test edit admin_users', function () {
        it('Test edit admin_users manually', async function () {
            await _setValueByUser('Any admin', false);
            await _setValueByUser('Admin users', ['user A', 'user B']);

            expect(store.state.scriptConfig.scriptConfig.admin_users).toEqual(['user A', 'user B'])
        });

        it('Test set any admin = false without any user, manually', async function () {
            await _setValueByUser('Any admin', false);

            expect(store.state.scriptConfig.scriptConfig.admin_users).toBeNil()
        });
    });

});
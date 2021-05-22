'use strict';

import ScriptConfig from '@/admin/components/scripts-config/ScriptConfig';
import ScriptConfigForm from '@/admin/components/scripts-config/ScriptConfigForm';
import {mount} from '@vue/test-utils';
import {assert, config as chaiConfig} from 'chai';
import Vuex from 'vuex';
import {attachToDocument, createScriptServerTestVue, vueTicks} from '../test_utils';
import {findField, setValueByUser} from './ParameterConfigForm_test';


chaiConfig.truncateThreshold = 0;

const localVue = createScriptServerTestVue();
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
                        scriptConfig: {'name': 'test_script', 'script_path': 'ping'}
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
            attachTo: attachToDocument(),
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
                'description': 'some desc',
                'working_directory': '/home',
                'requires_terminal': true,
                'include': 'script.json',
                'output_format': 'terminal'
            };

            await vueTicks();

            assert.equal('s1', _findField('Script name').value);
            assert.equal('important', _findField('Group').value);
            assert.equal('some desc', _findField('Description').value);
            assert.equal('/home', _findField('Working directory').value);
            assert.equal(true, _findField('Enable pseudo-terminal').value);
            assert.equal('script.json', _findField('Include config').value);
            assert.equal('terminal', _findField('Output format').value);

            expect(configComponent.get('.path-textfield input').element.value).toBe('ping')
        });
    });

    describe('Test edit config', function () {
        it('Test edit group', async function () {
            await _setValueByUser('Group', 'xyz');

            assert.equal('xyz', store.state.scriptConfig.scriptConfig.group);
        });
    });

    describe('Test edit script', function () {
        it('Test simple edit', async function () {
            await configComponent.get('.path-textfield input').setValue('echo 123')

            expect(store.state.scriptConfig.scriptConfig.script).toEqual({mode: 'new_path', path: 'echo 123'})
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

    describe('Test edit output_format', function () {
        it('Test edit output_format manually', async function () {
            await _setValueByUser('Output format', 'html');

            expect(store.state.scriptConfig.scriptConfig.output_format).toEqual('html')
        });
    });


});
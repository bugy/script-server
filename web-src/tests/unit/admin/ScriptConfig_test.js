'use strict';

import ScriptConfig from '@/admin/components/scripts-config/ScriptConfig';
import ScriptConfigForm from '@/admin/components/scripts-config/ScriptConfigForm';
import {mount} from '@vue/test-utils';
import Vuex from 'vuex';
import {attachToDocument, createScriptServerTestVue, vueTicks} from '../test_utils';
import {findField, setValueByUser} from './ParameterConfigForm_test';

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
        const form = configComponent.findComponent(ScriptConfigForm);
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

            expect(_findField('Script name').value).toBe('s1')
            expect(_findField('Group').value).toBe('important')
            expect(_findField('Description').value).toBe('some desc')
            expect(_findField('Working directory').value).toBe('/home')
            expect(_findField('Enable pseudo-terminal').value).toBe(true)
            expect(_findField('Include config').value).toBe('script.json')
            expect(_findField('Output format').value).toBe('terminal')

            expect(configComponent.get('.path-textfield input').element.value).toBe('ping')
        });

        async function runSchedulingConfigTest(
            config,
            expectedEnabled,
            expectedAutoCleanup,
            expectedCleanupDisabled,
            expectedValue) {
            store.state.scriptConfig.scriptConfig = config;

            await vueTicks();

            expect(_findField('Enabled').value).toBe(expectedEnabled)
            expect(_findField('Auto cleanup').value).toBe(expectedAutoCleanup)
            expect(_findField('Auto cleanup').disabled).toBe(expectedCleanupDisabled)

            expect(store.state.scriptConfig.scriptConfig.scheduling).toEqual(expectedValue)
        }

        it('Test show scheduling when no config', async function () {
            await runSchedulingConfigTest(
                {},
                false,
                undefined,
                true,
                undefined
            )
        })

        it('Test show scheduling when empty config', async function () {
            await runSchedulingConfigTest(
                {
                    'scheduling': {}
                },
                false,
                undefined,
                true,
                {}
            )
        })

        it('Test show scheduling when enabled', async function () {
            await runSchedulingConfigTest(
                {
                    'scheduling': {'enabled': true}
                },
                true,
                undefined,
                false,
                {'enabled': true}
            )
        })

        it('Test show scheduling when enabled and auto_cleanup', async function () {
            await runSchedulingConfigTest(
                {
                    'scheduling': {'enabled': true, 'auto_cleanup': true}
                },
                true,
                true,
                false,
                {'enabled': true, 'auto_cleanup': true}
            )
        })

        it('Test show scheduling when enabled and auto_cleanup and output_files', async function () {
            await runSchedulingConfigTest(
                {
                    'scheduling': {'enabled': true, 'auto_cleanup': true},
                    'output_files': ['test']
                },
                true,
                false,
                true,
                {'enabled': true}
            )
        })
    });

    describe('Test edit config', function () {
        it('Test edit group', async function () {
            await _setValueByUser('Group', 'xyz');

            expect(store.state.scriptConfig.scriptConfig.group).toBe('xyz')
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

    describe('Test show shared instances access', function () {
        it('Test show shared instances access unchecked', async function () {
            store.state.scriptConfig.scriptConfig = {};

            await vueTicks();

            expect(_findField('Shared Script Instances').value).toBe(false);
        });

        it('Test show shared instances access checked', async function () {
            store.state.scriptConfig.scriptConfig = {
                'access': {'shared_access': {'type': 'ALL_USERS'}}
            };

            await vueTicks();

            expect(_findField('Shared Script Instances').value).toBe(true);
        });
    });

    describe('Test edit global_instances', function () {
        it('Test update global_instances manually unchecked', async function () {
            await _setValueByUser('Shared Script Instances', false);

            expect(typeof store.state.scriptConfig.scriptConfig.access).toEqual('undefined');
        });

        it('Test update global_instances manually checked', async function () {
            await _setValueByUser('Shared Script Instances', true);

            expect(store.state.scriptConfig.scriptConfig.access).toEqual({'shared_access': {'type': 'ALL_USERS'}});
        });
    });

    describe('Test edit scheduling', function () {
        it('Test set enabled true', async function () {
            store.state.scriptConfig.scriptConfig = {};

            await vueTicks();

            await _setValueByUser('Enabled', true);

            expect(store.state.scriptConfig.scriptConfig.scheduling).toEqual({'enabled': true});
        });

        it('Test set enabled false', async function () {
            store.state.scriptConfig.scriptConfig = {'scheduling': {'enabled': true, 'auto_cleanup': true}};

            await vueTicks();

            await _setValueByUser('Enabled', false)

            expect(store.state.scriptConfig.scriptConfig.scheduling).toBeNil()
        });

        it('Test set auto cleanup enabled', async function () {
            store.state.scriptConfig.scriptConfig = {'scheduling': {'enabled': true}}

            await vueTicks()

            await _setValueByUser('Auto cleanup', true)

            expect(store.state.scriptConfig.scriptConfig.scheduling).toEqual({'enabled': true, 'auto_cleanup': true})
        });
    });

});
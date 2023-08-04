'use strict';

import ParameterConfigForm from '@/admin/components/scripts-config/ParameterConfigForm';
import ParameterValuesUiMapping from '@/admin/components/scripts-config/ParameterValuesUiMapping.vue';
import ScriptField from '@/admin/components/scripts-config/script-edit/ScriptField'
import ChipsList from '@/common/components/ChipsList';
import Combobox from '@/common/components/combobox';
import TextArea from '@/common/components/TextArea';
import Textfield from '@/common/components/textfield.vue';
import {asyncForEachKeyValue, isBlankString, isNull, setInputValue} from '@/common/utils/common';
import {mount} from '@vue/test-utils';
import {attachToDocument, createScriptServerTestVue, setChipListValue, vueTicks} from '../test_utils';

export async function setValueByUser(form, parameterName, value) {
    const childComponent = findField(form, parameterName);

    if (childComponent.$options._componentTag === ChipsList.name) {
        setChipListValue(childComponent, value);
        return;
    }

    const inputField = findFieldInputElement(form, parameterName);

    setInputValue(inputField, value, true);

    await vueTicks();
}

export const findField = (form, expectedName, failOnMissing = true) => {
    for (const child of form.$children) {
        let fieldName;
        if (child.$options._componentTag === ChipsList.name) {
            fieldName = child.title;
        } else if (child.$options._componentTag === ScriptField.name) {
            fieldName = child.scriptPathField.name;
        } else {
            fieldName = child.$props.config?.name;
        }

        if (!isNull(fieldName) && (fieldName.toLowerCase() === expectedName.toLowerCase())) {
            return child;
        }
    }

    if (failOnMissing) {
        throw Error('Failed to find field: ' + expectedName)
    }
};

export const findUiMappingFields = (form, failOnMissing = true) => {
    const mappingComponent = form.findComponent(ParameterValuesUiMapping)
    if (failOnMissing) {
        expect(mappingComponent.exists()).toBeTrue()
    }

    const result = []

    const textFields = mappingComponent.findAllComponents(Textfield);
    for (let i = 0; i < textFields.length; i += 2) {
        const scriptField = textFields.at(i)
        const uiField = textFields.at(i + 1)

        result.push([scriptField, uiField])
    }

    return result
}

export const extractUiMappingValues = (uiMappingFields) => {
    const result = []

    for (const uiMappingFieldPair of uiMappingFields) {
        const scriptValue = uiMappingFieldPair[0].vm.value
        const uiValue = uiMappingFieldPair[1].vm.value

        result.push([scriptValue, uiValue])
    }

    return result
}

export async function setUiMappingScriptValue(form, index, value) {
    const pair = findUiMappingFields(form)[index]

    setInputValue(pair[0].find('input').element, value, true)

    await vueTicks()
}

export async function setUiMappingUiValue(form, index, value) {
    const pair = findUiMappingFields(form)[index];

    setInputValue(pair[1].find('input').element, value, true)

    await vueTicks()
}

const findFieldInputElement = (form, expectedName) => {
    const field = findField(form, expectedName);

    let elementType;
    if (field.$options._componentTag === TextArea.name) {
        elementType = 'textarea';
    } else if (field.$options._componentTag === Combobox.name) {
        elementType = 'select';
    } else {
        elementType = 'input';
    }

    return $(field.$el).find(elementType).get(0);
};


describe('Test ParameterConfigForm', function () {
    let errors;
    let form;

    beforeEach(async function () {
        errors = [];

        form = mount(ParameterConfigForm, {
            localVue: createScriptServerTestVue(),
            attachTo: attachToDocument(),
            sync: false,
            propsData: {
                value: {
                    'name': 'param 1',
                    'description': 'some description'
                }
            }
        });
        form.vm.$parent.$forceUpdate();
        await form.vm.$nextTick();

        form.vm.$on('input', (value) => {
            form.setProps({value});
        });

        form.vm.$on('error', (error) => {
            errors.push(error);
        });
    });

    afterEach(async function () {
        await vueTicks();

        form.destroy();
    });

    const _findField = (expectedName, failOnMissing = true) => {
        return findField(form.vm, expectedName, failOnMissing);
    };

    const _findFieldInputElement = (expectedName) => {
        return findFieldInputElement(form.vm, expectedName);
    };

    async function _setValueByUser(parameterName, value) {
        await setValueByUser(form.vm, parameterName, value);
    }

    async function setPropsField(fieldName, value) {
        form.setProps({
            value: {
                ...form.vm.$props.value,
                [fieldName]: value
            }
        });
        await vueTicks();
    }

    const assertOutputValue = (fieldName, expectedValue) => {
        const actualValue = form.vm.$props.value[fieldName];
        expect(actualValue).toEqual(expectedValue)
    };

    const assertLastError = (fieldName, expectedError) => {
        const foundError = errors.slice().reverse().find(error => error.fieldName === fieldName);

        if (isBlankString(expectedError)) {
            expect(foundError?.message).toBeEmpty()
            return;
        }

        expect(foundError).not.toBeNil()

        expect(foundError.message).toBe(expectedError)
    };

    describe('Test initial values', function () {

        it('Test initial name', function () {
            const nameField = _findField('Name');

            expect(nameField.value).toBe('param 1')
        });

        it('Test simple parameters', async function () {
            form.setProps({
                value: {
                    name: 'param X',
                    description: 'my desc',
                    param: '-x',
                    type: 'int',
                    env_var: 'My_Param',
                    no_value: true,
                    required: true,
                    secure: true
                }
            });

            await vueTicks();

            expect(_findField('name').value).toBe('param X')
            expect(_findField('description').value).toBe('my desc')
            expect(_findField('param').value).toBe('-x')
            expect(_findField('type').value).toBe('int')
            expect(_findField('without value').value).toBe(true)
            expect(_findField('required').value).toBe(true)
            expect(_findField('constant', false)).toBeNil()
            expect(_findField('secret value').value).toBe(true)
            expect(_findField('env variable').value).toBe('My_Param')
        });

        it('Test simple parameters when int', async function () {
            form.setProps({
                value: {
                    type: 'int',
                    min: -5,
                    max: 1000
                }
            });

            await vueTicks();

            expect(_findField('type').value).toBe('int')
            expect(_findField('min').value.toString()).toBe('-5')
            expect(_findField('max').value.toString()).toBe('1000')
        });

        it('Test simple parameters when multiselect argument_per_value', async function () {
            form.setProps({
                value: {
                    type: 'multiselect',
                    multiselect_argument_type: 'argument_per_value'
                }
            });

            await vueTicks();

            expect(_findField('type').value).toBe('multiselect')
            expect(_findField('Value split type').value).toBe('argument_per_value')
            expect(_findField('separator', false)).toBeNil()
        });

        it('Test simple parameters when multiselect and single_argument', async function () {
            form.setProps({
                value: {
                    type: 'multiselect',
                    multiselect_argument_type: 'single_argument',
                    separator: '.'
                }
            });

            await vueTicks();

            expect(_findField('type').value).toBe('multiselect')
            expect(_findField('Value split type').value).toBe('single_argument')
            expect(_findField('separator').value).toBe('.')
        });

        it('Test simple parameters when server file', async function () {
            form.setProps({
                value: {
                    type: 'server_file',
                    file_dir: '/tmp/',
                    file_recursive: true,
                    file_type: 'dir',
                    file_extensions: ['txt', 'png']
                }
            });

            await vueTicks();

            expect(_findField('type').value).toBe('server_file')
            expect(_findField('file directory').value).toBe('/tmp/')
            expect(_findField('recursive').value).toBe(true)
            expect(_findField('file type').value).toBe('dir')
            expect(_findField('allowed file extensions').value).toEqual(['txt', 'png'])
        });

        it('Test default value when int', async function () {
            form.setProps({
                value: {
                    type: 'int',
                    default: 5
                }
            });

            await vueTicks();

            expect(_findField('default value').value).toBe('5')
        });

        it('Test default value when recursive file and default array', async function () {
            form.setProps({
                value: {
                    type: 'server_file',
                    default: ['some', 'path', 'value'],
                    file_recursive: true
                }
            });

            await vueTicks();

            expect(_findField('default value').value).toBe('some/path/value')
        });

        it('Test default value when recursive file and default array with absolute path', async function () {
            form.setProps({
                value: {
                    type: 'server_file',
                    default: ['/', 'some', 'path', 'value'],
                    file_recursive: true
                }
            });

            await vueTicks();

            expect(_findField('default value').value).toBe('/some/path/value')
        });

        it('Test default value when recursive file and default string', async function () {
            form.setProps({
                value: {
                    type: 'server_file',
                    default: '/tmp/script-server/files',
                    file_recursive: true
                }
            });

            await vueTicks();

            expect(_findField('default value').value).toBe('/tmp/script-server/files')
        });

        it('Test allowed values when array', async function () {
            form.setProps({
                value: {
                    type: 'list',
                    values: ['abc', '123', 'xyz']
                }
            });

            await vueTicks();

            expect(_findField('script', false)).toBeNil()
            expect(_findField('allowed values').value).toEqual(['abc', '123', 'xyz'])
            expect(_findField('load from script').value).toBeFalse()
            expect(_findField('enable bash operators', false)).toBeNil()
        });

        it('Test allowed values when script', async function () {
            form.setProps({
                value: {
                    type: 'list',
                    values: {'script': 'ls ~/'}
                }
            });

            await vueTicks();

            expect(_findField('script').value).toBe('ls ~/')
            expect(_findField('allowed values', false)).toBeNil()
            expect(_findField('load from script').value).toBeTrue()
            expect(_findField('enable bash operators').value).toBeFalse()
        });

        it('Test allowed values when array and type editable_list', async function () {
            form.setProps({
                value: {
                    type: 'editable_list',
                    values: ['abc', '123', 'xyz']
                }
            });

            await vueTicks();

            expect(_findField('script', false)).toBeNil()
            expect(_findField('allowed values').value).toEqual(['abc', '123', 'xyz'])
            expect(_findField('load from script').value).toBeFalse()
        });

        it('Test initial width weight', async function () {
            form.setProps({
                value: {
                    ui: {
                        'width_weight': 3
                    }
                }
            });

            await vueTicks()

            expect(_findField('UI width weight', false).value).toBe(3)
        });

        it('Test initial width weight when no config', async function () {
            form.setProps({
                value: {}
            });

            await vueTicks()

            expect(_findField('UI width weight', false).value).toBeNil()
        });

        it('Test initial separator', async function () {
            form.setProps({
                value: {
                    ui: {
                        'separator_before': {
                            'type': 'line',
                            'title': 'Some title'
                        }
                    }
                }
            });

            await vueTicks()

            expect(_findField('UI separator (before parameter)', false).value).toBe('line')
            expect(_findField('UI separator title', false).value).toBe('Some title')
        });

        it('Test initial width weight when no config', async function () {
            form.setProps({
                value: {}
            });

            await vueTicks()

            expect(_findField('UI separator (before parameter)', false).value).toBeNil()
            expect(_findField('UI separator title', false).value).toBeNil()
        });

        it('Test passAs when not set', async function () {
            form.setProps({
                value: {}
            });

            await vueTicks()

            expect(_findField('Pass as').value).toBe('argument + env_variable')
        });

        it('Test passAs when set', async function () {
            for (const passAs of ['argument', 'env_variable', 'stdin']) {
                form.setProps({
                    value: {'pass_as': passAs}
                });

                await vueTicks()

                expect(_findField('Pass as').value).toBe(passAs)
            }
        });

        it('Test stdin expected text', async function () {
            form.setProps({
                value: {
                    'pass_as': 'stdin',
                    'stdin_expected_text': '123'
                }
            });

            await vueTicks()

            expect(_findField('Stdin expected Text').value).toBe('123')
        });

        it('Test initial values UI mapping', async function () {
            form.setProps({
                value: {
                    'type': 'list',
                    'values_ui_mapping': {
                        'abc': 'qwerty',
                        ' def ': '1234'
                    }
                }
            });

            await vueTicks()

            expect(extractUiMappingValues(findUiMappingFields(form))).toEqual([
                ['abc', 'qwerty'],
                [' def ', '1234'],
                ['', '']
            ])
        });

    });

    describe('Test update values in form', function () {

        it('Test update name', async function () {
            await _setValueByUser('Name', 'abcde');

            assertOutputValue('name', 'abcde');
        });

        it('Test update description', async function () {
            await _setValueByUser('Description', 'some new description');

            assertOutputValue('description', 'some new description');
        });

        it('Test update param', async function () {
            await _setValueByUser('Param', '-p');

            assertOutputValue('param', '-p');
        });

        it('Test update env_var', async function () {
            await _setValueByUser('Env variable', 'Param_X');

            assertOutputValue('env_var', 'Param_X');
        });

        it('Test update type to int', async function () {
            await _setValueByUser('Type', 'int');

            assertOutputValue('type', 'int');
        });

        it('Test update type to list', async function () {
            await _setValueByUser('Type', 'list');

            assertOutputValue('type', 'list');
        });

        it('Test update no_value', async function () {
            await _setValueByUser('Without value', true);

            assertOutputValue('no_value', true);
        });

        it('Test update required', async function () {
            await _setValueByUser('Required', true);

            assertOutputValue('required', true);
        });

        it('Test update allowed values', async function () {
            await _setValueByUser('Type', 'list');

            await _setValueByUser('Allowed values', ['abc', '123', 'xyz']);

            assertOutputValue('values', ['abc', '123', 'xyz']);
        });

        it('Test update allowed values to script', async function () {
            await _setValueByUser('Type', 'list');
            await _setValueByUser('Load from script', true);

            await _setValueByUser('Script', 'ls ~/');

            assertOutputValue('values', {'script': 'ls ~/', 'shell': false});
        });

        it('Test update allowed values to script with shell', async function () {
            await _setValueByUser('Type', 'list');
            await _setValueByUser('Load from script', true);

            await _setValueByUser('Script', 'ls ~/');
            await _setValueByUser('Enable bash operators', true);

            assertOutputValue('values', {'script': 'ls ~/', 'shell': true});
        });

        it('Test update allowed values to script and back', async function () {
            await _setValueByUser('Type', 'list');

            await _setValueByUser('Allowed values', ['abc', '123', 'xyz']);

            await _setValueByUser('Load from script', true);

            await _setValueByUser('Script', 'ls ~/');

            await _setValueByUser('Load from script', false);

            assertOutputValue('values', ['abc', '123', 'xyz']);
        });

        it('Test update default when string', async function () {
            await _setValueByUser('Default value', 'xyz');


            assertOutputValue('default', 'xyz');
        });

        it('Test update default when multiselect', async function () {
            await _setValueByUser('Type', 'multiselect');

            await _setValueByUser('Default value', 'abc,123,xyz');

            assertOutputValue('default', ['abc', '123', 'xyz']);
        });

        it('Test update default when recursive file', async function () {
            await _setValueByUser('Type', 'server_file');
            await _setValueByUser('Recursive', true);

            await _setValueByUser('Default value', '/some/path/log.txt');

            assertOutputValue('default', ['/', 'some', 'path', 'log.txt']);
        });

        it('Test update min', async function () {
            await _setValueByUser('Type', 'int');

            await _setValueByUser('Min', 5);

            assertOutputValue('min', '5');
        });

        it('Test update max', async function () {
            await _setValueByUser('Type', 'int');

            await _setValueByUser('Max', 5);

            assertOutputValue('max', '5');
        });

        it('Test update constant', async function () {
            await _setValueByUser('Constant', true);

            assertOutputValue('constant', true);
        });

        it('Test update secure', async function () {
            await _setValueByUser('Secret value', true);

            assertOutputValue('secure', true);
        });

        it('Test update multiselect_argument_type', async function () {
            await _setValueByUser('Type', 'multiselect');

            await _setValueByUser('Value split type', 'repeat_param_value');

            assertOutputValue('multiselect_argument_type', 'repeat_param_value');
        });

        it('Test update separator', async function () {
            await _setValueByUser('Type', 'multiselect');

            await _setValueByUser('Separator', '.');

            assertOutputValue('separator', '.');
        });

        it('Test update file_dir', async function () {
            await _setValueByUser('Type', 'server_file');

            await _setValueByUser('File directory', '/tmp/logs');

            assertOutputValue('file_dir', '/tmp/logs');
        });

        it('Test update file_extensions', async function () {
            await _setValueByUser('Type', 'server_file');

            await _setValueByUser('Allowed file extensions', ['png', '.txt']);

            assertOutputValue('file_extensions', ['png', '.txt']);
        });

        it('Test update file_extensions to empty', async function () {
            await _setValueByUser('Type', 'server_file');

            await _setValueByUser('Allowed file extensions', ['png', '.txt']);
            await _setValueByUser('Allowed file extensions', []);

            assertOutputValue('file_extensions', undefined);
        });

        it('Test update file_recursive', async function () {
            await _setValueByUser('Type', 'server_file');

            await _setValueByUser('Recursive', true);

            assertOutputValue('file_recursive', true);
        });

        it('Test update excluded_files', async function () {
            await _setValueByUser('Type', 'server_file');

            await _setValueByUser('Excluded files', ['**/.passwd', 'auth']);

            assertOutputValue('excluded_files', ['**/.passwd', 'auth']);
        });

        it('Test update excluded_files to empty', async function () {
            await _setValueByUser('Type', 'server_file');

            await _setValueByUser('Excluded files', ['**/.passwd', 'auth']);
            await _setValueByUser('Excluded files', []);

            assertOutputValue('excluded_files', undefined);
        });

        it('Test update ui width weight', async function () {
            await _setValueByUser('UI width weight', 3);

            assertOutputValue('ui', {'width_weight': 3});
        });

        it('Test update ui width weight to empty', async function () {
            form.setProps({
                value: {
                    ui: {
                        'width_weight': 3
                    }
                }
            });

            await vueTicks()

            await _setValueByUser('UI width weight', null);

            assertOutputValue('ui', undefined);
        });

        it('Test update ui separator type only', async function () {
            await _setValueByUser('UI separator (before parameter)', 'line');

            assertOutputValue('ui', {'separator_before': {'type': 'line'}});
        });

        it('Test update ui separator title only', async function () {
            await _setValueByUser('UI separator title', 'Some title');

            assertOutputValue('ui', {'separator_before': {'title': 'Some title'}});
        });

        it('Test update ui separator type and title', async function () {
            await _setValueByUser('UI separator (before parameter)', 'new_line');
            await _setValueByUser('UI separator title', 'Another title');
            await _setValueByUser('Type', 'list');

            assertOutputValue('type', 'list')
            assertOutputValue('ui', {
                'separator_before': {
                    'type': 'new_line',
                    'title': 'Another title'
                }
            });
        });

        it('Test update ui separator to empty', async function () {
            form.setProps({
                value: {
                    ui: {
                        'separator_before': {
                            'type': 'line',
                            'title': 'Text'
                        }
                    }
                }
            });

            await vueTicks()

            await _setValueByUser('UI separator (before parameter)', 'none');
            await _setValueByUser('UI separator title', '  ');

            assertOutputValue('ui', undefined);
        });

        it('Test setting passAs values', async function () {
            const userInputToExpectedMap = {
                'argument + env_variable': undefined,
                'argument': 'argument',
                'env_variable': 'env_variable',
                'stdin': 'stdin'
            }

            await asyncForEachKeyValue(userInputToExpectedMap, async (userInput, expected) => {
                await _setValueByUser('Pass as', userInput);

                assertOutputValue('pass_as', expected);
            })
        })

        it('Test setting stdin expected text', async function () {
            await _setValueByUser('Pass as', 'stdin');
            await _setValueByUser('Stdin expected text', '123');

            assertOutputValue('stdin_expected_text', '123');
        })

        it('Test values_ui_mapping when type set to list', async function () {
            await _setValueByUser('Type', 'list');

            expect(findUiMappingFields(form).length).toEqual(1)
            assertOutputValue('values_ui_mapping', {});
        });

        it('Test values_ui_mapping when single empty ui value', async function () {
            await _setValueByUser('Type', 'list')

            await setUiMappingScriptValue(form, 0, 'abc')

            assertOutputValue('values_ui_mapping', {'abc': ''});
        });

        it('Test values_ui_mapping when multiple values', async function () {
            await _setValueByUser('Type', 'list')

            await setUiMappingScriptValue(form, 0, 'abc')
            await setUiMappingUiValue(form, 0, 'qwerty')

            await setUiMappingScriptValue(form, 1, ' def ')
            await setUiMappingUiValue(form, 1, ' 1234 ')

            await setUiMappingScriptValue(form, 2, 'hello')
            await setUiMappingUiValue(form, 2, 'world')

            assertOutputValue('values_ui_mapping', {
                'abc': 'qwerty',
                ' def ': ' 1234 ',
                'hello': 'world'
            });
            expect(extractUiMappingValues(findUiMappingFields(form))).toEqual([
                ['abc', 'qwerty'],
                [' def ', ' 1234 '],
                ['hello', 'world'],
                ['', '']
            ])
        });
    });

    describe('Test parameter dependencies', function () {

        it('Test type enabled when no_value false', async function () {
            const inputField = _findFieldInputElement('Type');
            expect(inputField.disabled).toBeFalse()
        });

        it('Test type disabled when no_value set by props', async function () {
            await setPropsField('no_value', true);

            const inputField = _findFieldInputElement('Type');
            expect(inputField.disabled).toBeTrue()
        });

        it('Test type disabled when no_value set by user', async function () {
            await _setValueByUser('Without value', true);

            const inputField = _findFieldInputElement('Type');
            expect(inputField.disabled).toBeTrue()
        });

        it('Test no constant and default when file_upload set via props', async function () {
            await setPropsField('type', 'file_upload');

            expect(_findField('Default value', false)).toBeNil()
            expect(_findField('Constant', false)).toBeNil()
        });

        it('Test no constant and default when file_upload set by user', async function () {
            await _setValueByUser('Type', 'file_upload');

            expect(_findField('Default value', false)).toBeNil()
            expect(_findField('Constant', false)).toBeNil()
        });

        it('Test no description when constant set via props', async function () {
            await setPropsField('constant', true);

            expect(_findField('Description', false)).toBeNil()
        });

        it('Test no description when constant set by user', async function () {
            await _setValueByUser('Constant', true);

            expect(_findField('Description', false)).toBeNil()
        });

        it('Test min max when type int set via props', async function () {
            await setPropsField('type', 'int');

            expect(_findField('Min')).not.toBeNil()
            expect(_findField('Max')).not.toBeNil()
        });

        it('Test min max when type int set by user', async function () {
            await _setValueByUser('Type', 'int');

            expect(_findField('Min')).not.toBeNil()
            expect(_findField('Max')).not.toBeNil()
        });

        it('Test min max when type int and no_value set vie props', async function () {
            await setPropsField('type', 'int');
            await setPropsField('no_value', true);

            expect(_findField('Min', false)).toBeNil()
            expect(_findField('Max', false)).toBeNil()
        });

        it('Test min max when type int and no_value set by user', async function () {
            await _setValueByUser('Type', 'int');
            await _setValueByUser('Without value', true);

            expect(_findField('Min', false)).toBeNil()
            expect(_findField('Max', false)).toBeNil()
        });

        it('Test multiselect fields when type multiselect set via props', async function () {
            await setPropsField('type', 'multiselect');

            expect(_findField('Value split type')).not.toBeNil()
            expect(_findField('Separator')).not.toBeNil()
        });

        it('Test multiselect fields when type multiselect set by user', async function () {
            await _setValueByUser('Type', 'multiselect');

            expect(_findField('Value split type')).not.toBeNil()
            expect(_findField('Separator')).not.toBeNil()
        });

        it('Test server_file fields when type server_file set via props', async function () {
            await _setValueByUser('type', 'server_file');

            expect(_findField('File directory')).not.toBeNil()
            expect(_findField('Recursive')).not.toBeNil()
            expect(_findField('File type')).not.toBeNil()
            expect(_findField('Allowed file extensions')).not.toBeNil()
        });

        it('Test server_file fields when type server_file set by user', async function () {
            await _setValueByUser('Type', 'server_file');

            expect(_findField('File directory')).not.toBeNil()
            expect(_findField('Recursive')).not.toBeNil()
            expect(_findField('File type')).not.toBeNil()
            expect(_findField('Allowed file extensions')).not.toBeNil()
        });

        it('Test "param" required when no_value set via props', async function () {
            await setPropsField('no_value', true);

            const argField = _findFieldInputElement('Param');
            expect(argField.required).toBeTrue()
        });

        it('Test "param" required when no_value set by user', async function () {
            await _setValueByUser('Without value', true);

            const argField = _findFieldInputElement('Param');
            expect(argField.required).toBeTrue()
        });

        it('Test "default" field when constant set via props', async function () {
            await setPropsField('constant', true);

            const argField = _findFieldInputElement('Constant value');
            expect(argField.required).toBeTrue()
        });

        it('Test "default" field when constant set by user', async function () {
            await _setValueByUser('Constant', true);

            const argField = _findFieldInputElement('Constant value');
            expect(argField.required).toBeTrue()
        });

        it('Test "max" field when min set via props', async function () {
            await setPropsField('type', 'int');
            await setPropsField('min', 5);

            await _setValueByUser('Max', 4);
            assertLastError('Max', 'min: 5');
        });

        it('Test "max" field when min set by user', async function () {
            await _setValueByUser('Type', 'int');
            await _setValueByUser('Min', 5);

            await _setValueByUser('Max', 4);
            assertLastError('Max', 'min: 5');
        });

        it('Test "max_length" field for default type', async function () {
            expect(_findField('Max characters length')).not.toBeNil()
        });

        it('Test "max_length" field for multiline_text type', async function () {
            await _setValueByUser('Type', 'multiline_text')

            expect(_findField('Max characters length')).not.toBeNil()
        });

        it('Test "max_length" field for int type', async function () {
            await _setValueByUser('Type', 'int')

            expect(_findField('Max characters length', false)).toBeNil()
        });
    });

    describe('Test errors', function () {

        it('Test name required when empty', async function () {
            await _setValueByUser('Name', '');

            assertLastError('Name', 'required');
        });

        it('Test name required when value', async function () {
            await _setValueByUser('Name', '');
            await _setValueByUser('Name', 'some script');

            assertLastError('Name', '');
        });

        it('Test allowed values from script required when empty', async function () {
            await setPropsField('type', 'list');
            await _setValueByUser('Load from script', true);

            assertLastError('Script', 'required');
        });

        it('Test allowed values from script required when value', async function () {
            await setPropsField('type', 'list');
            await _setValueByUser('Load from script', true);

            await _setValueByUser('Script', 'ls ~/');

            assertLastError('Script', '');
        });

        it('Test Param field required when no_value and value empty', async function () {
            await setPropsField('no_value', true);

            assertLastError('Param', 'required');
        });

        it('Test Param field required when no_value and value set', async function () {
            await setPropsField('no_value', true);

            await _setValueByUser('Param', '--flag');

            assertLastError('Param', '');
        });

        it('Test Default field required when constant and value empty', async function () {
            await setPropsField('constant', true);

            assertLastError('Constant value', 'required');
        });

        it('Test Default field required when constant and value set', async function () {
            await setPropsField('constant', true);

            await _setValueByUser('Constant value', 'abcde');

            assertLastError('Constant value', '');
        });
    });
});
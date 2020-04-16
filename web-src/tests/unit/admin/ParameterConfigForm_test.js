'use strict';

import ParameterConfigForm from '@/admin/components/scripts-config/ParameterConfigForm';
import ChipsList from '@/common/components/ChipsList';
import Combobox from '@/common/components/combobox';
import TextArea from '@/common/components/TextArea';
import {isBlankString, isNull, setInputValue} from '@/common/utils/common';
import {mount} from '@vue/test-utils';
import {assert, config as chaiConfig} from 'chai';
import {setChipListValue, vueTicks} from '../test_utils';

chaiConfig.truncateThreshold = 0;

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
        } else {
            fieldName = child.$props.config.name;
        }

        if (fieldName.toLowerCase() === expectedName.toLowerCase()) {
            return child;
        }
    }

    if (failOnMissing) {
        assert.fail('Failed to find field: ' + expectedName);
    }
};

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
            attachToDocument: true,
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
        assert.deepEqual(actualValue, expectedValue);
    };

    const assertLastError = (fieldName, expectedError) => {
        const foundError = errors.slice().reverse().find(error => error.fieldName === fieldName);

        if (isBlankString(expectedError)) {
            assert.isTrue(isNull(foundError) || isBlankString(foundError.message),
                'Expected no error, but was: ' + foundError.message);
            return;
        }

        if (isNull(foundError)) {
            assert.fail(null, expectedError, 'Expected error "' + expectedError + '", but no errors found')
        }

        assert.equal(foundError.message, expectedError);
    };

    describe('Test initial values', function () {

        it('Test initial name', function () {
            const nameField = _findField('Name');

            assert.equal('param 1', nameField.value);
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
                    constant: false,
                    secure: true
                }
            });

            await vueTicks();

            assert.equal('param X', _findField('name').value);
            assert.equal('my desc', _findField('description').value);
            assert.equal('-x', _findField('arg').value);
            assert.equal('int', _findField('type').value);
            assert.equal(true, _findField('without value').value);
            assert.equal(true, _findField('required').value);
            assert.equal(false, _findField('constant').value);
            assert.equal(true, _findField('secret value').value);
            assert.equal('My_Param', _findField('env variable').value);
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

            assert.equal('int', _findField('type').value);
            assert.equal(-5, _findField('min').value);
            assert.equal(1000, _findField('max').value);
        });

        it('Test simple parameters when multiselect', async function () {
            form.setProps({
                value: {
                    type: 'multiselect',
                    multiple_arguments: true,
                    separator: '.'
                }
            });

            await vueTicks();

            assert.equal('multiselect', _findField('type').value);
            assert.equal(true, _findField('as multiple arguments').value);
            assert.equal('.', _findField('separator').value);
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

            assert.equal('server_file', _findField('type').value);
            assert.equal('/tmp/', _findField('file directory').value);
            assert.equal(true, _findField('recursive').value);
            assert.equal('dir', _findField('file type').value);
            assert.deepEqual(['txt', 'png'], _findField('allowed file extensions').value);
        });

        it('Test default value when int', async function () {
            form.setProps({
                value: {
                    type: 'int',
                    default: 5
                }
            });

            await vueTicks();

            assert.equal(5, _findField('default value').value);
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

            assert.equal('some/path/value', _findField('default value').value);
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

            assert.equal('/some/path/value', _findField('default value').value);
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

            assert.equal('/tmp/script-server/files', _findField('default value').value);
        });

        it('Test allowed values when array', async function () {
            form.setProps({
                value: {
                    type: 'list',
                    values: ['abc', '123', 'xyz']
                }
            });

            await vueTicks();

            assert.isUndefined(_findField('script', false));
            assert.deepEqual(['abc', '123', 'xyz'], _findField('allowed values').value);
            assert.isFalse(_findField('load from script').value);
        });

        it('Test allowed values when script', async function () {
            form.setProps({
                value: {
                    type: 'list',
                    values: {'script': 'ls ~/'}
                }
            });

            await vueTicks();

            assert.equal('ls ~/', _findField('script').value);
            assert.isUndefined(_findField('allowed values', false));
            assert.isTrue(_findField('load from script').value);
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
            await _setValueByUser('Arg', '-p');

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

            assertOutputValue('values', {'script': 'ls ~/'});
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

        it('Test update multiple_arguments', async function () {
            await _setValueByUser('Type', 'multiselect');

            await _setValueByUser('As multiple arguments', true);

            assertOutputValue('multiple_arguments', true);
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

            await _setValueByUser('Allowed file extensions', []);

            assertOutputValue('file_extensions', undefined);
        });

        it('Test update file_recursive', async function () {
            await _setValueByUser('Type', 'server_file');

            await _setValueByUser('Recursive', true);

            assertOutputValue('file_recursive', true);
        });
    });

    describe('Test parameter dependencies', function () {

        it('Test type enabled when no_value false', async function () {
            const inputField = _findFieldInputElement('Type');
            assert.isFalse(inputField.disabled);
        });

        it('Test type disabled when no_value set by props', async function () {
            await setPropsField('no_value', true);

            const inputField = _findFieldInputElement('Type');
            assert.isTrue(inputField.disabled);
        });

        it('Test type disabled when no_value set by user', async function () {
            await _setValueByUser('Without value', true);

            const inputField = _findFieldInputElement('Type');
            assert.isTrue(inputField.disabled);
        });

        it('Test no constant and default when file_upload set via props', async function () {
            await setPropsField('type', 'file_upload');

            assert.isUndefined(_findField('Default value', false));
            assert.isUndefined(_findField('Constant', false));
        });

        it('Test no constant and default when file_upload set by user', async function () {
            await _setValueByUser('Type', 'file_upload');

            assert.isUndefined(_findField('Default value', false));
            assert.isUndefined(_findField('Constant', false));
        });

        it('Test no description when constant set via props', async function () {
            await setPropsField('constant', true);

            assert.isUndefined(_findField('Description', false));
        });

        it('Test no description when constant set by user', async function () {
            await _setValueByUser('Constant', true);

            assert.isUndefined(_findField('Description', false));
        });

        it('Test min max when type int set via props', async function () {
            await setPropsField('type', 'int');

            assert.isDefined(_findField('Min'));
            assert.isDefined(_findField('Max'));
        });

        it('Test min max when type int set by user', async function () {
            await _setValueByUser('Type', 'int');

            assert.isDefined(_findField('Min'));
            assert.isDefined(_findField('Max'));
        });

        it('Test min max when type int and no_value set vie props', async function () {
            await setPropsField('type', 'int');
            await setPropsField('no_value', true);

            assert.isUndefined(_findField('Min', false));
            assert.isUndefined(_findField('Max', false));
        });

        it('Test min max when type int and no_value set by user', async function () {
            await _setValueByUser('Type', 'int');
            await _setValueByUser('Without value', true);

            assert.isUndefined(_findField('Min', false));
            assert.isUndefined(_findField('Max', false));
        });

        it('Test multiselect fields when type multiselect set via props', async function () {
            await setPropsField('type', 'multiselect');

            assert.isDefined(_findField('As multiple arguments'));
            assert.isDefined(_findField('Separator'));
        });

        it('Test multiselect fields when type multiselect set by user', async function () {
            await _setValueByUser('Type', 'multiselect');

            assert.isDefined(_findField('As multiple arguments'));
            assert.isDefined(_findField('Separator'));
        });

        it('Test server_file fields when type multiselect set via props', async function () {
            await _setValueByUser('type', 'server_file');

            assert.isDefined(_findField('File directory'));
            assert.isDefined(_findField('Recursive'));
            assert.isDefined(_findField('File type'));
            assert.isDefined(_findField('Allowed file extensions'));
        });

        it('Test server_file fields when type multiselect set by user', async function () {
            await _setValueByUser('Type', 'server_file');

            assert.isDefined(_findField('File directory'));
            assert.isDefined(_findField('Recursive'));
            assert.isDefined(_findField('File type'));
            assert.isDefined(_findField('Allowed file extensions'));
        });

        it('Test "arg" required when no_value set via props', async function () {
            await setPropsField('no_value', true);

            const argField = _findFieldInputElement('Arg');
            assert.isTrue(argField.required);
        });

        it('Test "arg" required when no_value set by user', async function () {
            await _setValueByUser('Without value', true);

            const argField = _findFieldInputElement('Arg');
            assert.isTrue(argField.required);
        });

        it('Test "default" field when constant set via props', async function () {
            await setPropsField('constant', true);

            const argField = _findFieldInputElement('Constant value');
            assert.isTrue(argField.required);
        });

        it('Test "default" field when constant set by user', async function () {
            await _setValueByUser('Constant', true);

            const argField = _findFieldInputElement('Constant value');
            assert.isTrue(argField.required);
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

        it('Test Arg field required when no_value and value empty', async function () {
            await setPropsField('no_value', true);

            assertLastError('Arg', 'required');
        });

        it('Test Arg field required when no_value and value set', async function () {
            await setPropsField('no_value', true);

            await _setValueByUser('Arg', '--flag');

            assertLastError('Arg', '');
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
import {mount} from '@vue/test-utils'
import 'material-design-icons/iconfont/material-icons.css';
import {
    attachToDocument,
    awaitInvisible,
    awaitVisible,
    createScriptServerTestVue,
    timeout,
    vueTicks
} from '../../../test_utils'
import ScriptField from '@/admin/components/scripts-config/script-edit/ScriptField'
import 'materialize-css/js/dropdown'
import Vuex from 'vuex'
import Combobox from '@/common/components/combobox'
import {clearArray, isEmptyArray} from '@/common/utils/common'
import ace from 'ace-builds/src-noconflict/ace'
import {__RewireAPI__ as FileUploadRewire} from '@/common/components/file_upload'
import ScriptEditDialog from '@/admin/components/scripts-config/script-edit/ScriptEditDialog'
import MockAdapter from 'axios-mock-adapter'
import {axiosInstance} from '@/common/utils/axios_utils'

const localVue = createScriptServerTestVue();
localVue.use(Vuex);

function rewireFileUpload(filename) {
    const file = new File([''], filename)
    FileUploadRewire.__Rewire__('getFileInputValue', () => file);
}

const UPLOAD_MODE = 'Upload script'
const CODE_MODE = 'Edit script code'
const PATH_MODE = 'Path on server'

describe('Test ScriptField', function () {
    let scriptField
    let store
    let changes = []
    let axiosMock

    before(function () {
        M.Dropdown.defaults.inDuration = 1
        M.Dropdown.defaults.outDuration = 1
        M.Modal.defaults.inDuration = 1
        M.Modal.defaults.outDuration = 1
    })

    after(function () {
        M.Dropdown.defaults.inDuration = 150
        M.Dropdown.defaults.outDuration = 250
        M.Modal.defaults.inDuration = 250
        M.Modal.defaults.outDuration = 250
    })

    beforeEach(async function () {
        store = new Vuex.Store({
            modules: {
                auth: {
                    namespaced: true,
                    state: {
                        canEditCode: true
                    }
                }
            }
        })

        scriptField = createScriptField(store, localVue, changes, {
                originalPath: '',
                newConfig: true,
                configName: ''
            }
        )

        axiosMock = new MockAdapter(axiosInstance)
    })

    afterEach(async function () {
        await vueTicks();
        scriptField.destroy();

        clearArray(changes)
        __rewire_reset_all__()

        axiosMock.restore()
    });

    describe('Test simple edit', function () {

        it('Test initial path', function () {
            expect(scriptField.get('.input-field input').element.value).toBe('');
            expect(scriptField.get('.open-dialog-button').element).toBeVisible()
        });

        it('Test no button when no access', async function () {
            store.state.auth.canEditCode = false

            await vueTicks()

            expect(scriptField.find('.open-dialog-button').exists()).toBe(false)
        });

        it('Test change path by user', async function () {
            await scriptField.get('.input-field input').setValue('/new/path.py')

            expect(scriptField.get('.input-field input').element.value).toBe('/new/path.py');
            expect(changes).toEqual([{path: '/new/path.py', mode: 'new_path'}])
        });
    });

    describe('Test open dialog for new', function () {
        let dialogWrapper

        beforeEach(async function () {
            dialogWrapper = await openDialog()
        })

        it('Test initial path', async function () {
            assertPathModeOpen(dialogWrapper, '')
        })

        it('Test select code mode', async function () {
            await selectCodeMode(dialogWrapper)

            assertCodeModeOpen(dialogWrapper,
                './conf/scripts/{name}.py',
                '#!/usr/bin/env python\n',
                'python')
        });

        it('Test select upload mode', async function () {
            await selectUploadMode(dialogWrapper)

            assertUploadModeOpen(dialogWrapper, './conf/scripts/')
        });

        it('Test set path on server and save', async function () {
            await selectUploadMode(dialogWrapper)
            await selectPathMode(dialogWrapper)

            dialogWrapper.get('.textfield input').setValue('/some/new/path')
            await vueTicks()

            expect(dialogWrapper.find('.ignored-changes-warning').exists()).toBeFalse()

            await clickButton(dialogWrapper, 'Save')

            expect(changes).toEqual([{'mode': 'new_path', 'path': '/some/new/path'}])
            expect(scriptField.get('.input-field input').element.value).toBe('/some/new/path')
        })

        it('Test set code mode and save', async function () {
            await selectCodeMode(dialogWrapper)
            await clickButton(dialogWrapper, 'Save')

            expect(changes).toEqual([{
                mode: 'new_code',
                path: './conf/scripts/{name}.py',
                code: '#!/usr/bin/env python\n'
            }])
            expect(scriptField.get('.input-field input').element.value).toBe('./conf/scripts/{name}.py')
        })

        it('Test set code mode, edit and save', async function () {
            await selectCodeMode(dialogWrapper)

            await setCodeValue(dialogWrapper, 'abcdef')

            await dialogWrapper.findComponent(Combobox).get('select').setValue('R')

            expect(dialogWrapper.find('.ignored-changes-warning').exists()).toBeFalse()

            await clickButton(dialogWrapper, 'Save')

            expect(changes).toEqual([{
                mode: 'new_code',
                path: './conf/scripts/{name}.r',
                code: 'abcdef'
            }])
            expect(scriptField.get('.input-field input').element.value).toBe('./conf/scripts/{name}.r');
        })

        it('Test set upload mode, edit and save', async function () {
            await selectUploadMode(dialogWrapper)

            await setUploadFile(dialogWrapper, 'new_file.ps1')

            expect(dialogWrapper.find('.ignored-changes-warning').exists()).toBeFalse()

            await clickButton(dialogWrapper, 'Save')

            expect(changes).toEqual([{
                mode: 'upload_script',
                path: './conf/scripts/new_file.ps1',
                uploadFile: new File([''], 'new_file.ps1')
            }])
            expect(scriptField.get('.input-field input').element.value).toBe('./conf/scripts/new_file.ps1')
        })

        it('Test set path on server and cancel', async function () {
            dialogWrapper.get('.textfield input').setValue('/some/new/path')
            await vueTicks()

            await clickButton(dialogWrapper, 'Cancel')

            expect(changes).toEqual([])
            expect(scriptField.get('.input-field input').element.value).toBe('')
        })

        it('Test set code mode, edit and cancel', async function () {
            await selectCodeMode(dialogWrapper)

            await setCodeValue(dialogWrapper, 'abcdef')

            await dialogWrapper.findComponent(Combobox).setProps({value: 'bash'})

            await clickButton(dialogWrapper, 'Cancel')

            expect(changes).toEqual([])
            expect(scriptField.get('.input-field input').element.value).toBe('')
        })

        it('Test set upload mode, edit and cancel', async function () {
            await selectUploadMode(dialogWrapper)

            await setUploadFile(dialogWrapper, 'new_file.ps1')

            await clickButton(dialogWrapper, 'Cancel')

            expect(changes).toEqual([])
            expect(scriptField.get('.input-field input').element.value).toBe('')
        })

        it('Test edit config name for code mode', async function () {
            await scriptField.setProps({configName: 'new_name'})

            await selectCodeMode(dialogWrapper)

            verifyCodePath(dialogWrapper, './conf/scripts/new_name.py')

            await dialogWrapper.findComponent(Combobox).get('select').setValue('powershell')

            verifyCodePath(dialogWrapper, './conf/scripts/new_name.ps1')

            await clickButton(dialogWrapper, 'Save')

            expect(changes).toEqual([{
                mode: 'new_code',
                path: './conf/scripts/new_name.ps1',
                code: '#!/usr/bin/env pwsh\n'
            }])
            expect(scriptField.get('.input-field input').element.value).toBe('./conf/scripts/new_name.ps1')
        })

        it('Test edit config name for code mode after save', async function () {
            await scriptField.setProps({configName: 'new_name'})

            await selectCodeMode(dialogWrapper)

            await clickButton(dialogWrapper, 'Save')

            expect(changes).toEqual([{
                mode: 'new_code',
                path: './conf/scripts/new_name.py',
                code: '#!/usr/bin/env python\n'
            }])
            clearArray(changes)

            await scriptField.setProps({configName: 'another_name'})

            expect(changes).toEqual([{
                mode: 'new_code',
                path: './conf/scripts/another_name.py',
                code: '#!/usr/bin/env python\n'
            }])
            expect(scriptField.get('.input-field input').element.value).toBe('./conf/scripts/another_name.py')
        })

        it('Test disable save for empty path', async function () {
            await dialogWrapper.get('.textfield input').setValue('')

            expect(getDialogButton(dialogWrapper, 'Save').attributes('disabled')).toBe('disabled')
        })

        it('Test disable save for empty upload', async function () {
            await selectUploadMode(dialogWrapper)

            expect(getDialogButton(dialogWrapper, 'Save').attributes('disabled')).toBe('disabled')
        })

        it('Test enable save for empty code', async function () {
            await dialogWrapper.get('.textfield input').setValue('')

            await selectCodeMode(dialogWrapper)

            expect(getDialogButton(dialogWrapper, 'Save').attributes('disabled')).toBeNil()
        })

        it('Test non-active modifications in server path', async function () {
            await dialogWrapper.get('.textfield input').setValue('abc')

            await verifyWarningsOnlyWhenInactive(dialogWrapper, PATH_MODE)
        })

        it('Test non-active modifications in script code', async function () {
            await selectCodeMode(dialogWrapper)

            await setCodeValue(dialogWrapper, 'abcdef')

            await verifyWarningsOnlyWhenInactive(dialogWrapper, CODE_MODE)
        })

        it('Test non-active modifications in upload', async function () {
            await selectUploadMode(dialogWrapper)

            await setUploadFile(dialogWrapper, 'new_file.ps1')

            await verifyWarningsOnlyWhenInactive(dialogWrapper, UPLOAD_MODE)
        })
    });

    describe('Test open dialog for existing', function () {
        let dialogWrapper

        beforeEach(async function () {
            mockCodeLoad('Existing', 'some code')

            scriptField.destroy()

            scriptField = createScriptField(store, localVue, changes, {
                    originalPath: '/home/user/my_script.sh',
                    newConfig: false,
                    configName: 'Existing'
                }
            )

            dialogWrapper = await openDialog()
        })

        it('Test initial path', async function () {
            assertPathModeOpen(dialogWrapper, '/home/user/my_script.sh')
        })

        it('Test select code mode', async function () {
            await selectCodeMode(dialogWrapper)

            assertCodeModeOpen(dialogWrapper, '/home/user/my_script.sh', 'some code', 'bash')
        });

        it('Test select upload mode', async function () {
            await selectUploadMode(dialogWrapper)

            assertUploadModeOpen(dialogWrapper, '/home/user/my_script.sh')
        });

        it('Test set path on server and save', async function () {
            await selectUploadMode(dialogWrapper)
            await selectPathMode(dialogWrapper)

            dialogWrapper.get('.textfield input').setValue('/some/new/path')
            await vueTicks()

            await clickButton(dialogWrapper, 'Save')

            expect(changes).toEqual([{'mode': 'new_path', 'path': '/some/new/path'}])
            expect(scriptField.get('.input-field input').element.value).toBe('/some/new/path')
        })

        it('Test set code mode and save', async function () {
            await selectCodeMode(dialogWrapper)
            await clickButton(dialogWrapper, 'Save')

            expect(changes).toEqual([{
                mode: 'new_code',
                path: '/home/user/my_script.sh',
                code: 'some code'
            }])
            expect(scriptField.get('.input-field input').element.value).toBe('/home/user/my_script.sh')
        })

        it('Test set code mode, edit and save', async function () {
            await selectCodeMode(dialogWrapper)

            await setCodeValue(dialogWrapper, 'abcdef')

            await dialogWrapper.findComponent(Combobox).get('select').setValue('R')

            await clickButton(dialogWrapper, 'Save')

            expect(changes).toEqual([{
                mode: 'new_code',
                path: '/home/user/my_script.sh',
                code: 'abcdef'
            }])
            expect(scriptField.get('.input-field input').element.value).toBe('/home/user/my_script.sh');
        })

        it('Test set upload mode, edit and save', async function () {
            await selectUploadMode(dialogWrapper)

            await setUploadFile(dialogWrapper, 'new_file.ps1')

            await clickButton(dialogWrapper, 'Save')

            expect(changes).toEqual([{
                mode: 'upload_script',
                path: '/home/user/my_script.sh',
                uploadFile: new File([''], 'new_file.ps1')
            }])
            expect(scriptField.get('.input-field input').element.value).toBe('/home/user/my_script.sh')
        })

        it('Test set path on server and cancel', async function () {
            dialogWrapper.get('.textfield input').setValue('/some/new/path')
            await vueTicks()

            await clickButton(dialogWrapper, 'Cancel')

            expect(changes).toEqual([])
            expect(scriptField.get('.input-field input').element.value).toBe('/home/user/my_script.sh')
        })

        it('Test set code mode, edit and cancel', async function () {
            await selectCodeMode(dialogWrapper)

            await setCodeValue(dialogWrapper, 'abcdef')

            await dialogWrapper.findComponent(Combobox).setProps({value: 'bash'})

            await clickButton(dialogWrapper, 'Cancel')

            expect(changes).toEqual([])
            expect(scriptField.get('.input-field input').element.value).toBe('/home/user/my_script.sh')
        })

        it('Test set upload mode, edit and cancel', async function () {
            await selectUploadMode(dialogWrapper)

            await setUploadFile(dialogWrapper, 'new_file.ps1')

            await clickButton(dialogWrapper, 'Cancel')

            expect(changes).toEqual([])
            expect(scriptField.get('.input-field input').element.value).toBe('/home/user/my_script.sh')
        })

        it('Test edit config name for code mode', async function () {
            await scriptField.setProps({configName: 'new_name'})

            await selectCodeMode(dialogWrapper)

            verifyCodePath(dialogWrapper, '/home/user/my_script.sh')

            await dialogWrapper.findComponent(Combobox).get('select').setValue('powershell')

            verifyCodePath(dialogWrapper, '/home/user/my_script.sh')

            await clickButton(dialogWrapper, 'Save')

            expect(changes).toEqual([{
                mode: 'new_code',
                path: '/home/user/my_script.sh',
                code: 'some code'
            }])
            expect(scriptField.get('.input-field input').element.value).toBe('/home/user/my_script.sh')
        })

        it('Test edit config name for code mode after save', async function () {
            await scriptField.setProps({configName: 'new_name'})

            await selectCodeMode(dialogWrapper)

            await clickButton(dialogWrapper, 'Save')

            expect(changes).toEqual([{
                mode: 'new_code',
                path: '/home/user/my_script.sh',
                code: 'some code'
            }])
            clearArray(changes)

            await scriptField.setProps({configName: 'another_name'})

            expect(changes).toEqual([])
            expect(scriptField.get('.input-field input').element.value).toBe('/home/user/my_script.sh')
        })

        it('Test disable save for empty path', async function () {
            await dialogWrapper.get('.textfield input').setValue('')

            expect(getDialogButton(dialogWrapper, 'Save').attributes('disabled')).toBe('disabled')
        })

        it('Test disable save for empty upload', async function () {
            await selectUploadMode(dialogWrapper)

            expect(getDialogButton(dialogWrapper, 'Save').attributes('disabled')).toBe('disabled')
        })

        it('Test enable save for empty code', async function () {
            await dialogWrapper.get('.textfield input').setValue('')

            await selectCodeMode(dialogWrapper)

            expect(getDialogButton(dialogWrapper, 'Save').attributes('disabled')).toBeNil()
        })

        it('Test non-active modifications in server path', async function () {
            await dialogWrapper.get('.textfield input').setValue('abc')

            await verifyWarningsOnlyWhenInactive(dialogWrapper, PATH_MODE)
        })

        it('Test non-active modifications in script code', async function () {
            await selectCodeMode(dialogWrapper)

            await setCodeValue(dialogWrapper, 'abcdef')

            await verifyWarningsOnlyWhenInactive(dialogWrapper, CODE_MODE)
        })

        it('Test non-active modifications in upload', async function () {
            await selectUploadMode(dialogWrapper)

            await setUploadFile(dialogWrapper, 'new_file.ps1')

            await verifyWarningsOnlyWhenInactive(dialogWrapper, UPLOAD_MODE)
        })
    });

    describe('Test code loading errors', function () {
        let dialogWrapper

        beforeEach(async function () {
            scriptField.destroy()
        })

        async function init() {
            scriptField = createScriptField(store, localVue, changes, {
                    originalPath: '/home/user/my_script.sh',
                    newConfig: false,
                    configName: 'Existing'
                }
            )

            dialogWrapper = await openDialog()
        }

        it('Test soft error', async function () {
            mockCodeLoad('Existing', 'some code', 'some error')

            await init()

            await verifyCodeEditError('some error')
            await verifyUploadNoError()
        })

        it('Test 422 response', async function () {
            mockCodeLoadError('Existing', 422, 'Server exception')

            await init()

            await verifyCodeEditError('Server exception')
            await verifyUploadError('Server exception')
        })

        it('Test 403 response', async function () {
            mockCodeLoadError('Existing', 403, 'Cannot edit code')

            await init()

            await verifyCodeEditError('Cannot edit code')
            await verifyUploadError('Cannot edit code')
        })

        it('Test 500 response', async function () {
            mockCodeLoadError('Existing', 500, 'Anything')

            await init()

            await verifyCodeEditError('Could not load code, please check logs')
            await verifyUploadError('Could not load code, please check logs')
        })

        async function verifyCodeEditError(message) {
            await selectCodeMode(dialogWrapper)

            expect(dialogWrapper.get('.code-editor div.error').element).toBeVisible()
            expect(dialogWrapper.get('.code-editor div.error').text()).toBe(message)

            expect(dialogWrapper.get('.editor').element).not.toBeVisible()

            expect(getDialogButton(dialogWrapper, 'Save').attributes('disabled')).toBe('disabled')
        }

        async function verifyUploadNoError() {
            await selectUploadMode(dialogWrapper)

            expect(dialogWrapper.find('.script-uploader div.error').exists()).toBeFalse()

            expect(dialogWrapper.get('.file-upload-field').element).toBeVisible()
        }

        async function verifyUploadError(message) {
            await selectUploadMode(dialogWrapper)

            expect(dialogWrapper.get('.script-uploader div.error').element).toBeVisible()
            expect(dialogWrapper.get('.script-uploader div.error').text()).toBe(message)

            expect(dialogWrapper.find('.file-upload-field').exists()).toBeFalse()
        }
    })

    async function openDialog() {
        scriptField.get('.open-dialog-button').trigger('click')

        await timeout(5)

        const dialogWrapper = scriptField.findComponent(ScriptEditDialog)

        await awaitVisible(dialogWrapper.element, 1000)

        return dialogWrapper
    }

    async function selectMode(dialogWrapper, modeText) {
        for (let radio of dialogWrapper.findAll('.radio-group label').wrappers) {
            if (radio.get('span').text() === modeText) {
                radio.get('input').trigger('click')
                await timeout(5)
                return
            }
        }

        throw Error('Failed to find radio button for ' + modeText)
    }

    function getDialogButton(dialogWrapper, buttonText) {
        for (let button of dialogWrapper.findAll('.card-action .btn-flat').wrappers) {
            if (button.text() === buttonText) {
                return button
            }
        }
        throw Error('Failed to find button: ' + buttonText)
    }

    async function clickButton(dialogWrapper, buttonText) {
        const button = getDialogButton(dialogWrapper, buttonText)
        button.trigger('click')
        await awaitInvisible(dialogWrapper.element, 500)
    }

    function verifyRadioWarnings(dialogWrapper, expectedIndices) {
        let iconIndices = []
        let i = 0
        for (let radio of dialogWrapper.findAll('.radio-group p').wrappers) {
            const icon = radio.find('i.material-icons')
            if (icon.exists()) {
                iconIndices.push(i)
                expect(icon.text()).toBe('error_outline')
            }
            i++
        }

        expect(iconIndices).toEqual(expectedIndices)

        if (isEmptyArray(expectedIndices)) {
            expect(dialogWrapper.find('.ignored-changes-warning').exists()).toBeFalse()
        } else {
            expect(dialogWrapper.get('.ignored-changes-warning').text())
                .toBe('error_outline Changes in non-active tabs will be ignored')
        }
    }

    async function verifyWarningsOnlyWhenInactive(dialogWrapper, currentModeText) {
        verifyRadioWarnings(dialogWrapper, [])

        const modes = [PATH_MODE, CODE_MODE, UPLOAD_MODE]
        for (const mode of modes) {
            if (mode !== currentModeText) {
                await selectMode(dialogWrapper, mode)
                verifyRadioWarnings(dialogWrapper, [modes.indexOf(currentModeText)])
            }
        }

        await selectMode(dialogWrapper, currentModeText)
        verifyRadioWarnings(dialogWrapper, [])
    }

    async function selectCodeMode(dialogWrapper) {
        await selectMode(dialogWrapper, CODE_MODE)
    }

    async function selectUploadMode(dialogWrapper) {
        await selectMode(dialogWrapper, UPLOAD_MODE)
    }

    async function selectPathMode(dialogWrapper) {
        await selectMode(dialogWrapper, PATH_MODE)
    }

    async function setCodeValue(dialogWrapper, value) {
        const editor = ace.edit(dialogWrapper.get('.editor').element)
        editor.setValue(value)
        await vueTicks()
    }

    async function setUploadFile(dialogWrapper, filename) {
        rewireFileUpload(filename)
        await dialogWrapper.get('input[type=file]').trigger('change')
    }

    function verifyCodePath(dialogWrapper, path) {
        expect(dialogWrapper.get('.code-editor .textfield input').element.value).toBe(path)
    }

    function createScriptField(store, localVue, changes, props) {
        const scriptField = mount(ScriptField, {
            store,
            localVue,
            attachTo: attachToDocument(),
            propsData: props
        });

        scriptField.vm.$on('change', function (value) {
            changes.push(value)
        })

        return scriptField
    }

    function assertPathModeOpen(dialogWrapper, expectedPath) {
        expect(dialogWrapper.get('input[type=radio]:checked + span').text()).toBe(PATH_MODE)
        expect(dialogWrapper.get('.input-field input').element.value).toBe(expectedPath)

        expect(dialogWrapper.get('.code-editor').element).not.toBeVisible()
        expect(dialogWrapper.get('.script-uploader').element).not.toBeVisible()
    }

    function assertCodeModeOpen(dialogWrapper, expectedPath, expectedCode, expectedLanguage) {
        expect(dialogWrapper.get('.input-field input').element).not.toBeVisible()
        expect(dialogWrapper.get('.code-editor').element).toBeVisible()
        expect(dialogWrapper.findComponent(Combobox).props('value')).toBe(expectedLanguage)
        expect(dialogWrapper.get('.script-uploader').element).not.toBeVisible()
        expect(dialogWrapper.get('.editor').element).toBeVisible()

        expect(dialogWrapper.get('.code-editor input').element.value).toBe(expectedPath)
        const editor = ace.edit(dialogWrapper.get('.editor').element)
        expect(editor.getValue()).toBe(expectedCode)
    }

    function assertUploadModeOpen(dialogWrapper, expectedPath) {
        expect(dialogWrapper.get('.input-field input').element).not.toBeVisible()
        expect(dialogWrapper.get('.code-editor').element).not.toBeVisible()
        expect(dialogWrapper.get('.script-uploader .textfield input').element.value).toBe(expectedPath)
        expect(dialogWrapper.get('.script-uploader').element).toBeVisible()
    }

    function mockCodeLoad(configName, codeText, codeEditorError = null) {
        axiosMock.onGet('/admin/scripts/' + configName + '/code')
            .reply(200, {code: codeText, code_edit_error: codeEditorError});
    }

    function mockCodeLoadError(configName, status, errorText) {
        axiosMock.onGet('/admin/scripts/' + configName + '/code')
            .reply(status, errorText);
    }

})
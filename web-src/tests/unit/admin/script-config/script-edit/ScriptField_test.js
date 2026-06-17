import {mount} from '@vue/test-utils'
import 'material-design-icons/iconfont/material-icons.css';
import {
    attachToDocument,
    createScriptServerTestVue,
    timeout,
    vueTicks
} from '../../../test_utils'
import {createPinia, setActivePinia} from 'pinia';
import {useAuthStore} from '@/common/stores/auth';
import Combobox from '@/common/components/combobox'
import Textfield from '@/common/components/textfield'
import {clearArray, isEmptyArray} from '@/common/utils/common'
import ace from 'ace-builds/src-noconflict/ace'
import MockAdapter from 'axios-mock-adapter'
import {axiosInstance} from '@/common/utils/axios_utils'

// Vue 3 / Vitest replacement for babel-plugin-rewire: file_upload imports
// `getFileInputValue` from common utils to read the chosen <input type=file>.
// Mock just that export with a reconfigurable vi.fn (other utils preserved).
const {getFileInputValueMock} = vi.hoisted(() => ({getFileInputValueMock: vi.fn()}));
vi.mock('@/common/utils/common', async (importActual) => ({
    ...(await importActual()),
    getFileInputValue: getFileInputValueMock
}));

import ScriptField from '@/admin/components/scripts-config/script-edit/ScriptField'
import ScriptEditDialog from '@/admin/components/scripts-config/script-edit/ScriptEditDialog'

function rewireFileUpload(filename) {
    const file = new File([''], filename)
    getFileInputValueMock.mockImplementation(() => file);
}

const UPLOAD_MODE = 'Upload script'
const CODE_MODE = 'Edit script code'
const PATH_MODE = 'Path on server'

describe('Test ScriptField', function () {
    let scriptField
    let pinia
    let changes = []
    let axiosMock

    beforeEach(async function () {
        pinia = createPinia();
        setActivePinia(pinia);
        useAuthStore().canEditCode = true;

        scriptField = createScriptField(pinia, changes, {
                originalPath: '',
                newConfig: true,
                configName: ''
            }
        )

        axiosMock = new MockAdapter(axiosInstance)
    })

    afterEach(async function () {
        await vueTicks();
        scriptField.unmount();

        clearArray(changes)
        getFileInputValueMock.mockReset()

        axiosMock.restore()
    });

    describe('Test simple edit', function () {

        it('Test initial path', function () {
            expect(scriptField.get('.textfield input').element.value).toBe('');
            expect(scriptField.get('.open-dialog-button').element).toBeVisible()
        });

        it('Test no button when no access', async function () {
            useAuthStore().canEditCode = false

            await vueTicks()

            expect(scriptField.find('.open-dialog-button').exists()).toBe(false)
        });

        it('Test change path by user', async function () {
            await scriptField.get('.textfield input').setValue('/new/path.py')

            expect(scriptField.get('.textfield input').element.value).toBe('/new/path.py');
            expect(changes).toEqual([{path: '/new/path.py', mode: 'new_path'}])
        });
    });

    // ScriptEditDialog now uses v-dialog (Vuetify) which teleports its overlay to
    // document.body. DOM queries on dialog content use document.body.querySelector()
    // rather than VTU's find() (which only searches within a component's own element).
    // findComponent() still works for component-instance lookups across teleport.
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

            await dialogWrapper.findComponent(Textfield).find('input').setValue('/some/new/path')
            await vueTicks()

            expect(getDialogEl().querySelector('.ignored-changes-warning')).toBeNull()

            await clickButton(dialogWrapper, 'Save')

            expect(changes).toEqual([{'mode': 'new_path', 'path': '/some/new/path'}])
            expect(scriptField.get('.textfield input').element.value).toBe('/some/new/path')
        })

        it('Test set code mode and save', async function () {
            await selectCodeMode(dialogWrapper)
            await clickButton(dialogWrapper, 'Save')

            expect(changes).toEqual([{
                mode: 'new_code',
                path: './conf/scripts/{name}.py',
                code: '#!/usr/bin/env python\n'
            }])
            expect(scriptField.get('.textfield input').element.value).toBe('./conf/scripts/{name}.py')
        })

        it('Test set code mode, edit and save', async function () {
            await selectCodeMode(dialogWrapper)

            await setCodeValue(dialogWrapper, 'abcdef')

            dialogWrapper.findComponent(Combobox).vm.onUserInput('R')
            await vueTicks(3)

            expect(getDialogEl().querySelector('.ignored-changes-warning')).toBeNull()

            await clickButton(dialogWrapper, 'Save')

            expect(changes).toEqual([{
                mode: 'new_code',
                path: './conf/scripts/{name}.r',
                code: 'abcdef'
            }])
            expect(scriptField.get('.textfield input').element.value).toBe('./conf/scripts/{name}.r');
        })

        it('Test set upload mode, edit and save', async function () {
            await selectUploadMode(dialogWrapper)

            await setUploadFile(dialogWrapper, 'new_file.ps1')

            expect(getDialogEl().querySelector('.ignored-changes-warning')).toBeNull()

            await clickButton(dialogWrapper, 'Save')

            expect(changes).toEqual([{
                mode: 'upload_script',
                path: './conf/scripts/new_file.ps1',
                uploadFile: new File([''], 'new_file.ps1')
            }])
            expect(scriptField.get('.textfield input').element.value).toBe('./conf/scripts/new_file.ps1')
        })

        it('Test set path on server and cancel', async function () {
            await dialogWrapper.findComponent(Textfield).find('input').setValue('/some/new/path')
            await vueTicks()

            await clickButton(dialogWrapper, 'Cancel')

            expect(changes).toEqual([])
            expect(scriptField.get('.textfield input').element.value).toBe('')
        })

        it('Test set code mode, edit and cancel', async function () {
            await selectCodeMode(dialogWrapper)

            await setCodeValue(dialogWrapper, 'abcdef')

            dialogWrapper.findComponent(Combobox).vm.onUserInput('bash')
            await vueTicks(3)

            await clickButton(dialogWrapper, 'Cancel')

            expect(changes).toEqual([])
            expect(scriptField.get('.textfield input').element.value).toBe('')
        })

        it('Test set upload mode, edit and cancel', async function () {
            await selectUploadMode(dialogWrapper)

            await setUploadFile(dialogWrapper, 'new_file.ps1')

            await clickButton(dialogWrapper, 'Cancel')

            expect(changes).toEqual([])
            expect(scriptField.get('.textfield input').element.value).toBe('')
        })

        it('Test edit config name for code mode', async function () {
            await scriptField.setProps({configName: 'new_name'})

            await selectCodeMode(dialogWrapper)

            verifyCodePath(dialogWrapper, './conf/scripts/new_name.py')

            dialogWrapper.findComponent(Combobox).vm.onUserInput('powershell')
            await vueTicks(3)

            verifyCodePath(dialogWrapper, './conf/scripts/new_name.ps1')

            await clickButton(dialogWrapper, 'Save')

            expect(changes).toEqual([{
                mode: 'new_code',
                path: './conf/scripts/new_name.ps1',
                code: '#!/usr/bin/env pwsh\n'
            }])
            expect(scriptField.get('.textfield input').element.value).toBe('./conf/scripts/new_name.ps1')
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
            expect(scriptField.get('.textfield input').element.value).toBe('./conf/scripts/another_name.py')
        })

        it('Test disable save for empty path', async function () {
            await dialogWrapper.findComponent(Textfield).find('input').setValue('')

            expect(getDialogButton(dialogWrapper, 'Save')).toBeDisabled()
        })

        it('Test disable save for empty upload', async function () {
            await selectUploadMode(dialogWrapper)

            expect(getDialogButton(dialogWrapper, 'Save')).toBeDisabled()
        })

        it('Test enable save for empty code', async function () {
            await dialogWrapper.findComponent(Textfield).find('input').setValue('')

            await selectCodeMode(dialogWrapper)

            expect(getDialogButton(dialogWrapper, 'Save')).not.toBeDisabled()
        })

        it('Test non-active modifications in server path', async function () {
            await dialogWrapper.findComponent(Textfield).find('input').setValue('abc')

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

            scriptField.unmount()

            scriptField = createScriptField(pinia, changes, {
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

            await dialogWrapper.findComponent(Textfield).find('input').setValue('/some/new/path')
            await vueTicks()

            await clickButton(dialogWrapper, 'Save')

            expect(changes).toEqual([{'mode': 'new_path', 'path': '/some/new/path'}])
            expect(scriptField.get('.textfield input').element.value).toBe('/some/new/path')
        })

        it('Test set code mode and save', async function () {
            await selectCodeMode(dialogWrapper)
            await clickButton(dialogWrapper, 'Save')

            expect(changes).toEqual([{
                mode: 'new_code',
                path: '/home/user/my_script.sh',
                code: 'some code'
            }])
            expect(scriptField.get('.textfield input').element.value).toBe('/home/user/my_script.sh')
        })

        it('Test set code mode, edit and save', async function () {
            await selectCodeMode(dialogWrapper)

            await setCodeValue(dialogWrapper, 'abcdef')

            dialogWrapper.findComponent(Combobox).vm.onUserInput('R')
            await vueTicks(3)

            await clickButton(dialogWrapper, 'Save')

            expect(changes).toEqual([{
                mode: 'new_code',
                path: '/home/user/my_script.sh',
                code: 'abcdef'
            }])
            expect(scriptField.get('.textfield input').element.value).toBe('/home/user/my_script.sh');
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
            expect(scriptField.get('.textfield input').element.value).toBe('/home/user/my_script.sh')
        })

        it('Test set path on server and cancel', async function () {
            await dialogWrapper.findComponent(Textfield).find('input').setValue('/some/new/path')
            await vueTicks()

            await clickButton(dialogWrapper, 'Cancel')

            expect(changes).toEqual([])
            expect(scriptField.get('.textfield input').element.value).toBe('/home/user/my_script.sh')
        })

        it('Test set code mode, edit and cancel', async function () {
            await selectCodeMode(dialogWrapper)

            await setCodeValue(dialogWrapper, 'abcdef')

            dialogWrapper.findComponent(Combobox).vm.onUserInput('bash')
            await vueTicks(3)

            await clickButton(dialogWrapper, 'Cancel')

            expect(changes).toEqual([])
            expect(scriptField.get('.textfield input').element.value).toBe('/home/user/my_script.sh')
        })

        it('Test set upload mode, edit and cancel', async function () {
            await selectUploadMode(dialogWrapper)

            await setUploadFile(dialogWrapper, 'new_file.ps1')

            await clickButton(dialogWrapper, 'Cancel')

            expect(changes).toEqual([])
            expect(scriptField.get('.textfield input').element.value).toBe('/home/user/my_script.sh')
        })

        it('Test edit config name for code mode', async function () {
            await scriptField.setProps({configName: 'new_name'})

            await selectCodeMode(dialogWrapper)

            verifyCodePath(dialogWrapper, '/home/user/my_script.sh')

            dialogWrapper.findComponent(Combobox).vm.onUserInput('powershell')
            await vueTicks(3)

            verifyCodePath(dialogWrapper, '/home/user/my_script.sh')

            await clickButton(dialogWrapper, 'Save')

            expect(changes).toEqual([{
                mode: 'new_code',
                path: '/home/user/my_script.sh',
                code: 'some code'
            }])
            expect(scriptField.get('.textfield input').element.value).toBe('/home/user/my_script.sh')
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
            expect(scriptField.get('.textfield input').element.value).toBe('/home/user/my_script.sh')
        })

        it('Test disable save for empty path', async function () {
            await dialogWrapper.findComponent(Textfield).find('input').setValue('')

            expect(getDialogButton(dialogWrapper, 'Save')).toBeDisabled()
        })

        it('Test disable save for empty upload', async function () {
            await selectUploadMode(dialogWrapper)

            expect(getDialogButton(dialogWrapper, 'Save')).toBeDisabled()
        })

        it('Test enable save for empty code', async function () {
            await dialogWrapper.findComponent(Textfield).find('input').setValue('')

            await selectCodeMode(dialogWrapper)

            expect(getDialogButton(dialogWrapper, 'Save')).not.toBeDisabled()
        })

        it('Test non-active modifications in server path', async function () {
            await dialogWrapper.findComponent(Textfield).find('input').setValue('abc')

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
            scriptField.unmount()
        })

        async function init() {
            scriptField = createScriptField(pinia, changes, {
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
            const overlay = getDialogEl()

            const errorEl = overlay.querySelector('.code-editor .info-text.error')
            expect(errorEl).toBeVisible()
            expect(errorEl.textContent.trim()).toBe(message)

            expect(overlay.querySelector('.editor')).not.toBeVisible()

            expect(getDialogButton(dialogWrapper, 'Save')).toBeDisabled()
        }

        async function verifyUploadNoError() {
            await selectUploadMode(dialogWrapper)
            const overlay = getDialogEl()

            expect(overlay.querySelector('.script-uploader .info-text.error')).toBeNull()

            expect(overlay.querySelector('.file-upload-field')).toBeVisible()
        }

        async function verifyUploadError(message) {
            await selectUploadMode(dialogWrapper)
            const overlay = getDialogEl()

            const errorEl = overlay.querySelector('.script-uploader .info-text.error')
            expect(errorEl).toBeVisible()
            expect(errorEl.textContent.trim()).toBe(message)

            expect(overlay.querySelector('.file-upload-field')).toBeNull()
        }
    })

    // ── Helpers ──────────────────────────────────────────────────────────────

    async function openDialog() {
        scriptField.get('.open-dialog-button').trigger('click')
        await vueTicks(10)

        // ScriptEditDialog uses v-dialog (Vuetify) which teleports to document.body.
        // The :class on v-dialog lands on .v-overlay__content.
        const overlay = document.body.querySelector('.script-edit-dialog')
        expect(overlay).not.toBeNull()
        return scriptField.findComponent(ScriptEditDialog)
    }

    // Returns the live DOM element of the teleported dialog content.
    function getDialogEl() {
        return document.body.querySelector('.script-edit-dialog')
    }

    async function selectMode(dialogWrapper, modeText) {
        const overlay = getDialogEl()
        for (const radio of overlay.querySelectorAll('.radio-group .v-radio')) {
            const span = radio.querySelector('label span')
            if (span && span.textContent.trim() === modeText) {
                radio.querySelector('input[type=radio]').click()
                await timeout(50)
                return
            }
        }
        throw Error('Failed to find radio button for ' + modeText)
    }

    // Returns the raw <button> DOM element (not a VTU wrapper).
    function getDialogButton(dialogWrapper, buttonText) {
        const overlay = getDialogEl()
        for (const button of overlay.querySelectorAll('.v-card-actions button.v-btn')) {
            if (button.textContent.trim() === buttonText) {
                return button
            }
        }
        throw Error('Failed to find button: ' + buttonText)
    }

    async function clickButton(dialogWrapper, buttonText) {
        getDialogButton(dialogWrapper, buttonText).click()
        await vueTicks(10)
    }

    function verifyRadioWarnings(dialogWrapper, expectedIndices) {
        const overlay = getDialogEl()
        let iconIndices = []
        let i = 0
        for (const radio of overlay.querySelectorAll('.radio-group .v-radio')) {
            const icon = radio.querySelector('i.material-icons.option-icon')
            if (icon) {
                iconIndices.push(i)
                expect(icon.textContent.trim()).toBe('error_outline')
            }
            i++
        }

        expect(iconIndices).toEqual(expectedIndices)

        if (isEmptyArray(expectedIndices)) {
            expect(overlay.querySelector('.ignored-changes-warning')).toBeNull()
        } else {
            expect(overlay.querySelector('.ignored-changes-warning').textContent)
                .toContain('Changes in non-active tabs will be ignored')
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
        const editor = ace.edit(getDialogEl().querySelector('.editor'))
        editor.setValue(value)
        await vueTicks()
    }

    async function setUploadFile(dialogWrapper, filename) {
        rewireFileUpload(filename)
        const fileInput = getDialogEl().querySelector('input[type=file]')
        fileInput.dispatchEvent(new Event('change', {bubbles: true}))
        await vueTicks(3)
    }

    function verifyCodePath(dialogWrapper, path) {
        expect(getDialogEl().querySelector('.code-editor .textfield input').value).toBe(path)
    }

    function createScriptField(pinia, changes, props) {
        // Vue 3 removed vm.$on; register the 'change' listener via an onChange prop.
        const scriptField = mount(ScriptField, {
            global: {plugins: [pinia]},
            attachTo: attachToDocument(),
            props: {
                ...props,
                onChange: (value) => changes.push(value)
            }
        });

        // The component emits an initial 'change' during mount; the original test
        // attached its listener via $on *after* mount, so discard anything captured
        // up to this point to mirror that behaviour.
        changes.length = 0

        return scriptField
    }

    function assertPathModeOpen(dialogWrapper, expectedPath) {
        const overlay = getDialogEl()
        const activeRadio = overlay.querySelector('.radio-group .v-radio.active')
        expect(activeRadio?.querySelector('label span')?.textContent?.trim()).toBe(PATH_MODE)
        expect(overlay.querySelector('.textfield input').value).toBe(expectedPath)
        expect(overlay.querySelector('.code-editor')).not.toBeVisible()
        expect(overlay.querySelector('.script-uploader')).not.toBeVisible()
    }

    function assertCodeModeOpen(dialogWrapper, expectedPath, expectedCode, expectedLanguage) {
        const overlay = getDialogEl()
        // Path textfield is hidden; first .textfield is the path field (v-show=false in code mode)
        expect(overlay.querySelector('.textfield')).not.toBeVisible()
        expect(overlay.querySelector('.code-editor')).toBeVisible()
        // findComponent traverses the VNode tree and works across teleport boundaries
        expect(dialogWrapper.findComponent(Combobox).props('modelValue')).toBe(expectedLanguage)
        expect(overlay.querySelector('.script-uploader')).not.toBeVisible()
        expect(overlay.querySelector('.editor')).toBeVisible()

        expect(overlay.querySelector('.code-editor .textfield input').value).toBe(expectedPath)
        const editor = ace.edit(overlay.querySelector('.editor'))
        expect(editor.getValue()).toBe(expectedCode)
    }

    function assertUploadModeOpen(dialogWrapper, expectedPath) {
        const overlay = getDialogEl()
        expect(overlay.querySelector('.textfield')).not.toBeVisible()
        expect(overlay.querySelector('.code-editor')).not.toBeVisible()
        expect(overlay.querySelector('.script-uploader .textfield input').value).toBe(expectedPath)
        expect(overlay.querySelector('.script-uploader')).toBeVisible()
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

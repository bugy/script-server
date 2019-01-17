'use strict';

import {mount} from '@vue/test-utils';
import {assert, config as chaiConfig} from 'chai';
import {hasClass, isEmptyArray, toMap} from '../js/common';
import FileDialog from '../js/components/file_dialog'
import {triggerDoubleClick, triggerKeyEvent, triggerSingleClick, vueTicks} from './test_utils';

chaiConfig.truncateThreshold = 0;

describe('Test FileDialog', function () {
    beforeEach(function () {
        this.dialogClosed = false;
        this.chosenPath = null;
        this.loadFiles = function (path) {
            const prefix = isEmptyArray(path)
                ? ''
                : path.map(p => p[p.indexOf('_') + 1]).reduce((p1, p2) => p1 + p2) + '_';

            return [
                {name: prefix + 'admin.log', type: 'file'},
                {name: prefix + 'temp', type: 'dir'},
                {name: prefix + 'private', type: 'dir', readable: false},
                {name: prefix + 'logs', type: 'dir'},
                {name: prefix + 'passwords.txt', type: 'file'}
            ]
        };

        this.fileDialog = mount(FileDialog, {
            attachToDocument: true,
            propsData: {
                onClose: () => this.dialogClosed = true,
                onFileSelect: (path) => this.chosenPath = path,
                loadFiles: this.loadFiles
            }
        });
    });

    afterEach(async function () {
        this.fileDialog.destroy();
    });

    function getFileElements(fileDialog) {
        return $(fileDialog.element).find('li').toArray();
    }

    function getFileElementName(element) {
        return $(element).find('span').text();
    }

    function getFileElementType(element) {
        return $(element).find('i').text();
    }

    function getDisplayedFileNames(fileDialog) {
        const fileElements = getFileElements(fileDialog);
        return fileElements.map(getFileElementName);
    }

    function findFileElement(filename, fileDialog) {
        return getFileElements(fileDialog).find(element => (getFileElementName(element) === filename));
    }

    function findActiveFileElement(fileDialog) {
        return getFileElements(fileDialog).find(element => hasClass(element, 'active'));
    }

    async function navigateTo(path, fileDialog) {
        fileDialog.vm.setChosenFile([...path, '']);
        await vueTicks();
    }

    function getBreadcrumbElements(fileDialog) {
        return $(fileDialog.element).find('a.breadcrumb').toArray();
    }

    function findBreadcrumbElement(path, fileDialog) {
        const pathElements = getBreadcrumbElements(fileDialog);
        return pathElements.find(element => element.innerText === path);
    }

    function getBreadcrumbNames(fileDialog) {
        const elements = getBreadcrumbElements(fileDialog);
        return elements.map(element => element.innerText);
    }

    describe('Test file display', function () {

        it('Test root folder', async function () {
            const expectedFiles = this.loadFiles([]).map(file => file.name);

            await vueTicks();

            const displayedNames = getDisplayedFileNames(this.fileDialog);

            assert.sameMembers(expectedFiles, displayedNames);
        });

        it('Test order', async function () {
            const expectedFiles = [
                'logs',
                'private',
                'temp',
                'admin.log',
                'passwords.txt'];

            await vueTicks();

            const displayedNames = getDisplayedFileNames(this.fileDialog);

            assert.sameMembers(expectedFiles, displayedNames);
        });

        it('Test file types', async function () {
            const expectedFileTypes = {
                'logs': 'folder',
                'private': 'lock',
                'temp': 'folder',
                'admin.log': 'description',
                'passwords.txt': 'description'
            };

            await vueTicks();

            const elements = getFileElements(this.fileDialog);
            var fileTypes = toMap(elements, getFileElementName, getFileElementType);

            assert.deepEqual(fileTypes, expectedFileTypes);
        });

        it('Test level 1', async function () {
            const path = ['logs'];
            const expectedFiles = this.loadFiles(path).map(file => file.name);

            await navigateTo(path, this.fileDialog);

            const displayedNames = getDisplayedFileNames(this.fileDialog);

            assert.sameMembers(expectedFiles, displayedNames);
        });

        it('Test level 4', async function () {
            const path = ['logs', 'l_temp', 'lt_temp', 'ltt_logs'];

            const expectedFiles = this.loadFiles(path).map(file => file.name);
            await navigateTo(path, this.fileDialog);

            const displayedNames = getDisplayedFileNames(this.fileDialog);

            assert.sameMembers(expectedFiles, displayedNames);
        });
    });

    describe('Test navigation', function () {

        it('Test double click dir', async function () {
            await vueTicks();

            const logsElement = findFileElement('logs', this.fileDialog);
            triggerDoubleClick(logsElement);

            assert.sameOrderedMembers(this.fileDialog.vm.path, ['logs'])
        });

        it('Test double click dir twice', async function () {
            await vueTicks();

            const logsElement = findFileElement('logs', this.fileDialog);
            triggerDoubleClick(logsElement);

            await vueTicks();

            const tempElement = findFileElement('l_temp', this.fileDialog);
            triggerDoubleClick(tempElement);

            assert.sameOrderedMembers(this.fileDialog.vm.path, ['logs', 'l_temp'])
        });

        it('Test navigate on setChosenFile', async function () {
            this.fileDialog.vm.setChosenFile(['temp', 't_logs', '']);

            await vueTicks();

            assert.sameOrderedMembers(this.fileDialog.vm.path, ['temp', 't_logs'])
        });

        it('Test navigate breadcrumbs to home', async function () {
            await navigateTo(['temp', 't_logs'], this.fileDialog);

            const homeElement = findBreadcrumbElement('home', this.fileDialog);
            triggerSingleClick(homeElement);

            assert.sameOrderedMembers(this.fileDialog.vm.path, [])
        });

        it('Test navigate breadcrumbs to same', async function () {
            await navigateTo(['temp', 't_logs'], this.fileDialog);

            const homeElement = findBreadcrumbElement('t_logs', this.fileDialog);
            triggerSingleClick(homeElement);

            assert.sameOrderedMembers(this.fileDialog.vm.path, ['temp', 't_logs'])
        });

        it('Test navigate breadcrumbs to previous', async function () {
            await navigateTo(['temp', 't_logs'], this.fileDialog);

            const homeElement = findBreadcrumbElement('temp', this.fileDialog);
            triggerSingleClick(homeElement);

            assert.sameOrderedMembers(this.fileDialog.vm.path, ['temp'])
        });

        it('Test navigate ellipsized breadcrumbs to same', async function () {
            await navigateTo(['temp', 't_temp', 'tt_temp', 'ttt_logs', 'tttl_temp'], this.fileDialog);

            const homeElement = findBreadcrumbElement('tttl_temp', this.fileDialog);
            triggerSingleClick(homeElement);

            assert.sameOrderedMembers(this.fileDialog.vm.path, ['temp', 't_temp', 'tt_temp', 'ttt_logs', 'tttl_temp'])
        });

        it('Test navigate ellipsized breadcrumbs to previous', async function () {
            await navigateTo(['temp', 't_temp', 'tt_temp', 'ttt_logs', 'tttl_temp'], this.fileDialog);

            const homeElement = findBreadcrumbElement('ttt_logs', this.fileDialog);
            triggerSingleClick(homeElement);

            assert.sameOrderedMembers(this.fileDialog.vm.path, ['temp', 't_temp', 'tt_temp', 'ttt_logs'])
        });

        it('Test navigate ellipsized breadcrumbs to ellipsis', async function () {
            await navigateTo(['temp', 't_temp', 'tt_temp', 'ttt_logs', 'tttl_temp'], this.fileDialog);

            const homeElement = findBreadcrumbElement('...', this.fileDialog);
            triggerSingleClick(homeElement);

            assert.sameOrderedMembers(this.fileDialog.vm.path, ['temp', 't_temp', 'tt_temp'])
        });

        it('Test navigate on backspace', async function () {
            await navigateTo(['temp', 't_logs'], this.fileDialog);

            triggerKeyEvent(this.fileDialog.element, 'keyup', 8);

            assert.sameOrderedMembers(this.fileDialog.vm.path, ['temp'])
        });

        it('Test navigate on enter', async function () {
            await vueTicks();

            triggerSingleClick(findFileElement('logs', this.fileDialog));
            triggerKeyEvent(this.fileDialog.element, 'keypress', 13);

            assert.sameOrderedMembers(this.fileDialog.vm.path, ['logs'])
        });
    });

    describe('Test breadcrumbs', function () {

        it('Test root breadcrumbs', async function () {
            await vueTicks();

            const breadcrumbs = getBreadcrumbNames(this.fileDialog);
            assert.sameOrderedMembers(breadcrumbs, ['home'])
        });

        it('Test breadcrumbs with 1 level', async function () {
            const dir = 'logs';
            await navigateTo([dir], this.fileDialog);

            const breadcrumbs = getBreadcrumbNames(this.fileDialog);
            assert.sameOrderedMembers(breadcrumbs, ['home', dir])
        });

        it('Test breadcrumbs with 2 levels', async function () {
            const path = ['logs', 'l_temp'];
            await navigateTo(path, this.fileDialog);

            const breadcrumbs = getBreadcrumbNames(this.fileDialog);
            assert.sameOrderedMembers(breadcrumbs, ['home', ...path])
        });

        it('Test breadcrumbs with 3 levels', async function () {
            const path = ['logs', 'l_temp', 'lt_temp'];
            await navigateTo(path, this.fileDialog);

            const breadcrumbs = getBreadcrumbNames(this.fileDialog);
            assert.sameOrderedMembers(breadcrumbs, ['home', ...path])
        });

        it('Test breadcrumbs with 4 levels', async function () {
            await navigateTo(['temp', 't_temp', 'tt_temp', 'ttt_logs', 'tttl_temp'], this.fileDialog);

            const breadcrumbs = getBreadcrumbNames(this.fileDialog);
            assert.sameOrderedMembers(breadcrumbs, ['home', '...', 'ttt_logs', 'tttl_temp'])
        });

        it('Test breadcrumbs with 5 levels', async function () {
            await navigateTo(['temp', 't_temp', 'tt_temp', 'ttt_logs', 'tttl_temp', 'tttlt_temp'], this.fileDialog);

            const breadcrumbs = getBreadcrumbNames(this.fileDialog);
            assert.sameOrderedMembers(breadcrumbs, ['home', '...', 'tttl_temp', 'tttlt_temp'])
        });
    });

    describe('Test selection', function () {

        it('Test initial selection', async function () {
            await vueTicks();

            assert.isNull(this.fileDialog.vm.selectedFile)
        });

        it('Test select on click', async function () {
            await vueTicks();

            const filename = 'passwords.txt';
            triggerSingleClick(findFileElement(filename, this.fileDialog));

            assert.equal(this.fileDialog.vm.selectedFile.name, filename);
        });

        it('Test select element', async function () {
            await vueTicks();

            const filename = 'admin.log';
            triggerSingleClick(findFileElement(filename, this.fileDialog));
            await vueTicks();

            const activeElement = findActiveFileElement(this.fileDialog);

            assert.isNotNull(activeElement);
            assert.equal(getFileElementName(activeElement), filename);
        });

        it('Test select element on setChosenFile', async function () {
            const filename = 'tl_private';

            this.fileDialog.vm.setChosenFile(['temp', 't_logs', filename]);
            await vueTicks();

            const activeElement = findActiveFileElement(this.fileDialog);

            assert.isNotNull(activeElement);
            assert.equal(getFileElementName(activeElement), filename);
        });

        it('Test unselect element on setChosenFile([])', async function () {
            this.fileDialog.vm.setChosenFile(['temp', 't_logs', 'tl_private']);
            await vueTicks();

            this.fileDialog.vm.setChosenFile([]);
            await vueTicks();

            const activeElement = findActiveFileElement(this.fileDialog);
            assert.isUndefined(activeElement);
        });

        it('Test select element on setChosenFile, when not opened', async function () {
            this.fileDialog.setProps({opened: false});

            const filename = 'l_temp';

            this.fileDialog.vm.setChosenFile(['logs', filename]);
            await vueTicks();

            this.fileDialog.setProps({opened: true});
            await vueTicks();

            const activeElement = findActiveFileElement(this.fileDialog);

            assert.isNotNull(activeElement);
            assert.equal(getFileElementName(activeElement), filename);
        });
    });
});
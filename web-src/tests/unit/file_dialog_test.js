'use strict';

import FileDialog from '@/common/components/file_dialog'
import {hasClass, isEmptyArray, toMap} from '@/common/utils/common';
import {mount} from '@vue/test-utils';
import {attachToDocument, triggerDoubleClick, triggerKeyEvent, triggerSingleClick, vueTicks} from './test_utils';

describe('Test FileDialog', function () {
    let chosenPath, dialogClosed, fileDialog, loadFiles;

    beforeEach(function () {
        dialogClosed = false;
        chosenPath = null;
        loadFiles = function (path) {
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

        fileDialog = mount(FileDialog, {
            attachTo: attachToDocument(),
            props: {
                onClose: () => dialogClosed = true,
                onFileSelect: (path) => chosenPath = path,
                loadFiles: loadFiles
            }
        });
    });

    afterEach(async function () {
        fileDialog.unmount();
    });

    function getFileElements(fileDialog) {
        return [...fileDialog.element.querySelectorAll('li')];
    }

    function getFileElementName(element) {
        return element.querySelector('span')?.textContent ?? '';
    }

    function getFileElementType(element) {
        return element.querySelector('i')?.textContent ?? '';
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
        return [...fileDialog.element.querySelectorAll('a.breadcrumb')];
    }

    function findBreadcrumbElement(path, fileDialog) {
        const pathElements = getBreadcrumbElements(fileDialog);
        return pathElements.find(element => element.textContent === path);
    }

    function getBreadcrumbNames(fileDialog) {
        const elements = getBreadcrumbElements(fileDialog);
        return elements.map(element => element.textContent);
    }

    describe('Test file display', function () {

        it('Test root folder', async function () {
            const expectedFiles = loadFiles([]).map(file => file.name);

            await vueTicks();

            const displayedNames = getDisplayedFileNames(fileDialog);

            expect(expectedFiles).toIncludeSameMembers(displayedNames);
        });

        it('Test order', async function () {
            const expectedFiles = [
                'logs',
                'private',
                'temp',
                'admin.log',
                'passwords.txt'];

            await vueTicks();

            const displayedNames = getDisplayedFileNames(fileDialog);

            expect(expectedFiles).toEqual(displayedNames);
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

            const elements = getFileElements(fileDialog);
            var fileTypes = toMap(elements, getFileElementName, getFileElementType);

            expect(fileTypes).toEqual(expectedFileTypes);
        });

        it('Test level 1', async function () {
            const path = ['logs'];
            const expectedFiles = loadFiles(path).map(file => file.name);

            await navigateTo(path, fileDialog);

            const displayedNames = getDisplayedFileNames(fileDialog);

            expect(expectedFiles).toIncludeSameMembers(displayedNames);
        });

        it('Test level 4', async function () {
            const path = ['logs', 'l_temp', 'lt_temp', 'ltt_logs'];

            const expectedFiles = loadFiles(path).map(file => file.name);
            await navigateTo(path, fileDialog);

            const displayedNames = getDisplayedFileNames(fileDialog);

            expect(expectedFiles).toIncludeSameMembers(displayedNames);
        });
    });

    describe('Test navigation', function () {

        it('Test double click dir', async function () {
            await vueTicks();

            const logsElement = findFileElement('logs', fileDialog);
            triggerDoubleClick(logsElement);

            expect(fileDialog.vm.path).toEqual(['logs'])
        });

        it('Test double click dir twice', async function () {
            await vueTicks();

            const logsElement = findFileElement('logs', fileDialog);
            triggerDoubleClick(logsElement);

            await vueTicks();

            const tempElement = findFileElement('l_temp', fileDialog);
            triggerDoubleClick(tempElement);

            expect(fileDialog.vm.path).toEqual(['logs', 'l_temp'])
        });

        it('Test navigate on setChosenFile', async function () {
            fileDialog.vm.setChosenFile(['temp', 't_logs', '']);

            await vueTicks();

            expect(fileDialog.vm.path).toEqual(['temp', 't_logs'])
        });

        it('Test navigate breadcrumbs to home', async function () {
            await navigateTo(['temp', 't_logs'], fileDialog);

            const homeElement = findBreadcrumbElement('home', fileDialog);
            triggerSingleClick(homeElement);

            expect(fileDialog.vm.path).toEqual([])
        });

        it('Test navigate breadcrumbs to same, when 1 level', async function () {
            await navigateTo(['temp'], fileDialog);

            const homeElement = findBreadcrumbElement('temp', fileDialog);
            triggerSingleClick(homeElement);

            expect(fileDialog.vm.path).toEqual(['temp'])
        });

        it('Test navigate breadcrumbs to same', async function () {
            await navigateTo(['temp', 't_logs'], fileDialog);

            const homeElement = findBreadcrumbElement('t_logs', fileDialog);
            triggerSingleClick(homeElement);

            expect(fileDialog.vm.path).toEqual(['temp', 't_logs'])
        });

        it('Test navigate breadcrumbs to previous', async function () {
            await navigateTo(['temp', 't_logs'], fileDialog);

            const homeElement = findBreadcrumbElement('temp', fileDialog);
            triggerSingleClick(homeElement);

            expect(fileDialog.vm.path).toEqual(['temp'])
        });

        it('Test navigate ellipsized breadcrumbs to same', async function () {
            await navigateTo(['temp', 't_temp', 'tt_temp', 'ttt_logs', 'tttl_temp'], fileDialog);

            const homeElement = findBreadcrumbElement('tttl_temp', fileDialog);
            triggerSingleClick(homeElement);

            expect(fileDialog.vm.path).toEqual(['temp', 't_temp', 'tt_temp', 'ttt_logs', 'tttl_temp'])
        });

        it('Test navigate ellipsized breadcrumbs to previous', async function () {
            await navigateTo(['temp', 't_temp', 'tt_temp', 'ttt_logs', 'tttl_temp'], fileDialog);

            const homeElement = findBreadcrumbElement('ttt_logs', fileDialog);
            triggerSingleClick(homeElement);

            expect(fileDialog.vm.path).toEqual(['temp', 't_temp', 'tt_temp', 'ttt_logs'])
        });

        it('Test navigate ellipsized breadcrumbs to ellipsis', async function () {
            await navigateTo(['temp', 't_temp', 'tt_temp', 'ttt_logs', 'tttl_temp'], fileDialog);

            const homeElement = findBreadcrumbElement('...', fileDialog);
            triggerSingleClick(homeElement);

            expect(fileDialog.vm.path).toEqual(['temp', 't_temp', 'tt_temp'])
        });

        it('Test navigate on backspace', async function () {
            await navigateTo(['temp', 't_logs'], fileDialog);

            triggerKeyEvent(fileDialog.element, 'keyup', 8);

            expect(fileDialog.vm.path).toEqual(['temp'])
        });

        it('Test navigate on enter', async function () {
            await vueTicks();

            triggerSingleClick(findFileElement('logs', fileDialog));
            triggerKeyEvent(fileDialog.element, 'keypress', 13);

            expect(fileDialog.vm.path).toEqual(['logs'])
        });
    });

    describe('Test breadcrumbs', function () {

        it('Test root breadcrumbs', async function () {
            await vueTicks();

            const breadcrumbs = getBreadcrumbNames(fileDialog);
            expect(breadcrumbs).toEqual(['home'])
        });

        it('Test breadcrumbs with 1 level', async function () {
            const dir = 'logs';
            await navigateTo([dir], fileDialog);

            const breadcrumbs = getBreadcrumbNames(fileDialog);
            expect(breadcrumbs).toEqual(['home', dir])
        });

        it('Test breadcrumbs with 2 levels', async function () {
            const path = ['logs', 'l_temp'];
            await navigateTo(path, fileDialog);

            const breadcrumbs = getBreadcrumbNames(fileDialog);
            expect(breadcrumbs).toEqual(['home', ...path])
        });

        it('Test breadcrumbs with 3 levels', async function () {
            const path = ['logs', 'l_temp', 'lt_temp'];
            await navigateTo(path, fileDialog);

            const breadcrumbs = getBreadcrumbNames(fileDialog);
            expect(breadcrumbs).toEqual(['home', ...path])
        });

        it('Test breadcrumbs with 4 levels', async function () {
            await navigateTo(['temp', 't_temp', 'tt_temp', 'ttt_logs', 'tttl_temp'], fileDialog);

            const breadcrumbs = getBreadcrumbNames(fileDialog);
            expect(breadcrumbs).toEqual(['home', '...', 'ttt_logs', 'tttl_temp'])
        });

        it('Test breadcrumbs with 5 levels', async function () {
            await navigateTo(['temp', 't_temp', 'tt_temp', 'ttt_logs', 'tttl_temp', 'tttlt_temp'], fileDialog);

            const breadcrumbs = getBreadcrumbNames(fileDialog);
            expect(breadcrumbs).toEqual(['home', '...', 'tttl_temp', 'tttlt_temp'])
        });
    });

    describe('Test selection', function () {

        it('Test initial selection', async function () {
            await vueTicks();

            expect(fileDialog.vm.selectedFile).toBeNil()
        });

        it('Test select on click', async function () {
            await vueTicks();

            const filename = 'passwords.txt';
            triggerSingleClick(findFileElement(filename, fileDialog));

            expect(fileDialog.vm.selectedFile.name).toBe(filename)
        });

        it('Test select element', async function () {
            await vueTicks();

            const filename = 'admin.log';
            triggerSingleClick(findFileElement(filename, fileDialog));
            await vueTicks();

            const activeElement = findActiveFileElement(fileDialog);

            expect(activeElement).not.toBeNil()
            expect(getFileElementName(activeElement)).toBe(filename)
        });

        it('Test select element on setChosenFile', async function () {
            const filename = 'tl_private';

            fileDialog.vm.setChosenFile(['temp', 't_logs', filename]);
            await vueTicks();

            const activeElement = findActiveFileElement(fileDialog);

            expect(activeElement).not.toBeNil()
            expect(getFileElementName(activeElement)).toBe(filename)
        });

        it('Test unselect element on setChosenFile([])', async function () {
            fileDialog.vm.setChosenFile(['temp', 't_logs', 'tl_private']);
            await vueTicks();

            fileDialog.vm.setChosenFile([]);
            await vueTicks();

            const activeElement = findActiveFileElement(fileDialog);
            expect(activeElement).toBeNil()
        });

        it('Test select element on setChosenFile, when not opened', async function () {
            fileDialog.setProps({opened: false});

            const filename = 'l_temp';

            fileDialog.vm.setChosenFile(['logs', filename]);
            await vueTicks();

            fileDialog.setProps({opened: true});
            await vueTicks();

            const activeElement = findActiveFileElement(fileDialog);

            expect(activeElement).not.toBeNil()
            expect(getFileElementName(activeElement)).toBe(filename)
        });
    });
});
'use strict';

import ParamListItem from '@/admin/components/scripts-config/ParamListItem';
import ScriptParamList from '@/admin/components/scripts-config/ScriptParamList';
import ParameterConfigForm from '@/admin/components/scripts-config/ParameterConfigForm';
import {createVue, timeout, triggerSingleClick, vueTicks} from '../test_utils';
import {setValueByUser} from './ParameterConfigForm_test';


describe('Test ScriptParamList', function () {
    let list;
    let errors;

    beforeEach(async function () {
        errors = [];

        list = createVue(
            ScriptParamList, {
                parameters: [
                    {
                        'name': 'param 1',
                        'description': 'some description'
                    },
                    {
                        'name': 'param 2'
                    },
                    {
                        'name': 'param 3'
                    }]
            },
        );
        await list.vm.$nextTick();
    });

    afterEach(async function () {
        await vueTicks();

        list.unmount();
    });

    function findParamItem(paramName) {
        return list.findAllComponents(ParamListItem)
            .find(item => item.props('param')?.name === paramName) || null;
    }

    function clickOnParam(paramName) {
        const found = list.findAllComponents(ParamListItem)
            .find(item => item.props('param')?.name === paramName);
        expect(found).not.toBeNil();
        list.vm.openedPanel = found.props('panelValue');
    }

    function assertOpen(paramName) {
        const found = list.findAllComponents(ParamListItem)
            .find(item => item.props('param')?.name === paramName);
        expect(found).not.toBeNil();
        expect(list.vm.openedPanel).toBe(found.props('panelValue'));
    }

    function assertClosed(paramName) {
        const found = list.findAllComponents(ParamListItem)
            .find(item => item.props('param')?.name === paramName);
        expect(found).not.toBeNil();
        expect(list.vm.openedPanel).not.toBe(found.props('panelValue'));
    }

    function getButton(item, buttonName) {
        const icon = [...item.element.querySelectorAll('i')]
            .find(e => e.textContent.trim() === buttonName);
        return icon?.closest('button');
    }

    async function clickParamAction(paramName, action) {
        const item = findParamItem(paramName);

        const button = getButton(item, action);
        triggerSingleClick(button);

        await vueTicks();
    }

    async function setValue(paramName, fieldName, value) {
        await vueTicks();  // wait for panel content to render after clickOnParam

        const paramItem = findParamItem(paramName);
        expect(paramItem).not.toBeNil()

        const paramForm = paramItem.findComponent(ParameterConfigForm);
        await setValueByUser(paramForm, fieldName, value)
    }

    describe('Test visualisation', function () {
        it('Test show parameters list', async function () {
            expect(findParamItem('param 1')).not.toBeNil()
            expect(findParamItem('param 2')).not.toBeNil()
            expect(findParamItem('param 3')).not.toBeNil()
        });

        it('Test show add param button', async function () {
            const button = list.element.querySelector('.add-param-item');
            expect(button).not.toBeNil()
        });

        it('Test expand parameter', async function () {
            clickOnParam('param 1');

            assertOpen('param 1');
        });

        it('Test expand another parameter', async function () {
            clickOnParam('param 1');
            clickOnParam('param 2');

            assertOpen('param 2');
            assertClosed('param 1');
        });

        it('Test parameter title after prop change', async function () {
            list.vm.parameters[1].name = 'new name';

            expect(findParamItem('new name')).not.toBeNil()
        });
    });

    describe('Test move parameters', function () {
        it('Test move 2nd parameter up', async function () {
            await clickParamAction('param 2', 'arrow_upward');

            expect(list.vm.parameters[0].name).toBe('param 2')
        });

        it('Test move 2nd parameter up twice', async function () {
            await clickParamAction('param 2', 'arrow_upward');
            await clickParamAction('param 2', 'arrow_upward');

            expect(list.vm.parameters[0].name).toBe('param 2')
        });

        it('Test move 2nd parameter up and then first', async function () {
            await clickParamAction('param 2', 'arrow_upward');
            await clickParamAction('param 1', 'arrow_upward');

            expect(list.vm.parameters[0].name).toBe('param 1')
            expect(list.vm.parameters[1].name).toBe('param 2')
        });

        it('Test move 3rd parameter up twice', async function () {
            await clickParamAction('param 3', 'arrow_upward');
            await clickParamAction('param 3', 'arrow_upward');

            expect(list.vm.parameters[0].name).toBe('param 3')
            expect(list.vm.parameters[1].name).toBe('param 1')
            expect(list.vm.parameters[2].name).toBe('param 2')
        });

        it('Test move 2nd parameter down', async function () {
            await clickParamAction('param 2', 'arrow_downward');

            expect(list.vm.parameters[2].name).toBe('param 2')
        });

        it('Test move 2nd parameter down twice', async function () {
            await clickParamAction('param 2', 'arrow_downward');
            await clickParamAction('param 2', 'arrow_downward');

            expect(list.vm.parameters[2].name).toBe('param 2')
        });

        it('Test move 2nd parameter down and then last', async function () {
            await clickParamAction('param 2', 'arrow_downward');
            await clickParamAction('param 3', 'arrow_downward');

            expect(list.vm.parameters[1].name).toBe('param 2')
            expect(list.vm.parameters[2].name).toBe('param 3')
        });

        it('Test move first parameter down twice', async function () {
            await clickParamAction('param 1', 'arrow_downward');
            await clickParamAction('param 1', 'arrow_downward');

            expect(list.vm.parameters[0].name).toBe('param 2')
            expect(list.vm.parameters[1].name).toBe('param 3')
            expect(list.vm.parameters[2].name).toBe('param 1')
        });

        it('Test move open parameter up', async function () {
            clickOnParam('param 2');

            await clickParamAction('param 2', 'arrow_upward');

            assertOpen('param 2');
            assertClosed('param 1');
        });

        it('Test move open parameter down', async function () {
            clickOnParam('param 2');
            await clickParamAction('param 2', 'arrow_downward');

            assertOpen('param 2');
            assertClosed('param 3');
        });

        it('Test move closed parameter up to an open one', async function () {
            clickOnParam('param 2');
            await clickParamAction('param 3', 'arrow_upward');

            assertOpen('param 2');
            assertClosed('param 3');
        });

        it('Test move closed parameter down to an open one', async function () {
            clickOnParam('param 2');
            await clickParamAction('param 1', 'arrow_downward');

            assertOpen('param 2');
            assertClosed('param 1');
        });
    });

    describe('Test delete parameters', function () {
        it('Test delete parameter in the beginning', async function () {
            await clickParamAction('param 1', 'delete');

            await vueTicks();

            expect(findParamItem('param 1')).toBeNil()
            expect(findParamItem('param 2')).not.toBeNil()
            expect(findParamItem('param 3')).not.toBeNil()
        });

        it('Test delete parameter in the middle', async function () {
            await clickParamAction('param 2', 'delete');

            expect(findParamItem('param 1')).not.toBeNil()
            expect(findParamItem('param 2')).toBeNil()
            expect(findParamItem('param 3')).not.toBeNil()
        });

        it('Test delete parameter in the end', async function () {
            await clickParamAction('param 3', 'delete');

            expect(findParamItem('param 1')).not.toBeNil()
            expect(findParamItem('param 2')).not.toBeNil()
            expect(findParamItem('param 3')).toBeNil()
        });

        it('Test delete open parameter', async function () {
            clickOnParam('param 2');
            await clickParamAction('param 2', 'delete');

            assertClosed('param 1');
            assertClosed('param 3');
        });

        it('Test delete parameter after opened', async function () {
            clickOnParam('param 1');
            await clickParamAction('param 2', 'delete');

            assertOpen('param 1');
            assertClosed('param 3');
        });

        it('Test delete parameter before opened', async function () {
            clickOnParam('param 3');
            await clickParamAction('param 2', 'delete');

            assertClosed('param 1');
            assertOpen('param 3');
        });

        it('Test open snackbar on delete', async function () {
            await clickParamAction('param 2', 'delete');

            expect(list.vm.snackbarVisible).toBeTrue();
            expect(list.vm.snackbarMessage).toBe('Deleted param 2');
        });

        it('Test queue multiple deletes', async function () {
            await clickParamAction('param 2', 'delete');
            await clickParamAction('param 1', 'delete');
            await clickParamAction('param 3', 'delete');

            expect(list.vm.snackbarVisible).toBeTrue();
            expect(list.vm.undoQueue.length).toBe(3);
            expect(list.vm.undoQueue[0].param.name).toBe('param 2');
            expect(list.vm.undoQueue[1].param.name).toBe('param 1');
            expect(list.vm.undoQueue[2].param.name).toBe('param 3');
        });

        it('Test undo delete', async function () {
            await clickParamAction('param 2', 'delete');

            list.vm.undoDelete();
            await vueTicks();

            expect(findParamItem('param 2')).not.toBeNil()
            expect(list.vm.parameters[0].name).toBe('param 1')
            expect(list.vm.parameters[1].name).toBe('param 2')
            expect(list.vm.parameters[2].name).toBe('param 3')
        });

        it('Test undo first delete after multiple deletes', async function () {
            await clickParamAction('param 2', 'delete');
            await clickParamAction('param 1', 'delete');
            await clickParamAction('param 3', 'delete');

            list.vm.undoDelete();
            await vueTicks();

            expect(findParamItem('param 2')).not.toBeNil()
            expect(list.vm.parameters[0].name).toBe('param 2')
        });
    });

    describe('Test edit parameter', function () {

        it('Test set missing value', async function () {
            clickOnParam('param 1');
            assertOpen('param 1');

            await setValue('param 1', 'type', 'int');
            assertOpen('param 1');
            expect(list.vm.parameters[0].type).toBe('int')
        });
    });

    describe('Test add parameter', function () {
        const clickAddButton = () => {
            const addParamButton = list.element.querySelector('.add-param-item');
            triggerSingleClick(addParamButton);
        };

        it('Test add parameter', async function () {
            clickAddButton();

            await vueTicks();

            expect(list.vm.parameters.length).toBe(4)
            expect(list.vm.parameters[3].name).toBe(undefined)

            list.vm.openingNewParam = false;
            await timeout(100);
        });

        it('Test add multiple parameters', async function () {
            clickAddButton();
            clickAddButton();
            clickAddButton();

            await vueTicks();

            expect(list.vm.parameters.length).toBe(6)
            expect(list.vm.parameters[3].name).toBe(undefined)
            expect(list.vm.parameters[4].name).toBe(undefined)
            expect(list.vm.parameters[5].name).toBe(undefined)

            list.vm.openingNewParam = false;
            await timeout(100);
        });
    });

});

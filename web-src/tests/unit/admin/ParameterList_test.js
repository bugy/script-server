'use strict';

import ParamListItem from '@/admin/components/scripts-config/ParamListItem';
import ScriptParamList from '@/admin/components/scripts-config/ScriptParamList';
import {hasClass} from '@/common/utils/common';
import {createScriptServerTestVue, createVue, timeout, triggerSingleClick, vueTicks} from '../test_utils';
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
            null,
            createScriptServerTestVue());
        await list.$nextTick();
    });

    afterEach(async function () {
        await vueTicks();

        list.$el.parentNode.removeChild(list.$el);
        list.$destroy();
    });

    function findParamItem(paramName) {
        let foundChild = null;
        for (const child of list.$children) {
            if (!child.$options || (child.$options._componentTag !== ParamListItem.name)) {
                continue;
            }

            const currentParamName = child.$props.param.name;
            if (currentParamName === paramName) {
                foundChild = child;
                break;
            }
        }
        return foundChild;
    }

    function clickOnParam(paramName) {
        let paramItem = findParamItem(paramName);
        expect(paramItem).not.toBeNil()

        const index = list.$children.indexOf(paramItem);
        M.Collapsible.getInstance(list.$el).open(index);
    }

    function assertOpen(paramName) {
        let paramItem = findParamItem(paramName);
        expect(paramItem).not.toBeNil()

        expect(hasClass(paramItem.$el, 'active')).toBeTrue()
    }

    function getButton(item, buttonName) {
        return $(item.$el).find('a:has(i:contains(' + buttonName + '))').get(0);
    }

    async function clickParamAction(paramName, action) {
        const item = findParamItem(paramName);
        const button = getButton(item, action);
        triggerSingleClick(button);

        await vueTicks();
    }

    function assertClosed(paramName) {
        let paramItem = findParamItem(paramName);
        expect(paramItem).not.toBeNil()

        expect(hasClass(paramItem.$el, 'active')).toBeFalse()
    }

    async function setValue(paramName, fieldName, value) {
        let paramItem = findParamItem(paramName);
        expect(paramItem).not.toBeNil()

        const paramForm = paramItem.$children[0];
        await setValueByUser(paramForm, fieldName, value)
    }

    describe('Test visualisation', function () {
        it('Test show parameters list', async function () {
            expect(findParamItem('param 1')).not.toBeNil()
            expect(findParamItem('param 2')).not.toBeNil()
            expect(findParamItem('param 3')).not.toBeNil()
        });

        it('Test show add param button', async function () {
            const button = $(list.$el).find('li.add-param-item').get(0);
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
            list.$props.parameters[1].name = 'new name';

            expect(findParamItem('new name')).not.toBeNil()
        });
    });

    describe('Test move parameters', function () {
        it('Test move 2nd parameter up', async function () {
            await clickParamAction('param 2', 'arrow_upward');

            expect(list.$props.parameters[0].name).toBe('param 2')
        });

        it('Test move 2nd parameter up twice', async function () {
            await clickParamAction('param 2', 'arrow_upward');
            await clickParamAction('param 2', 'arrow_upward');

            expect(list.$props.parameters[0].name).toBe('param 2')
        });

        it('Test move 2nd parameter up and then first', async function () {
            await clickParamAction('param 2', 'arrow_upward');
            await clickParamAction('param 1', 'arrow_upward');

            expect(list.$props.parameters[0].name).toBe('param 1')
            expect(list.$props.parameters[1].name).toBe('param 2')
        });

        it('Test move 3rd parameter up twice', async function () {
            await clickParamAction('param 3', 'arrow_upward');
            await clickParamAction('param 3', 'arrow_upward');

            expect(list.$props.parameters[0].name).toBe('param 3')
            expect(list.$props.parameters[1].name).toBe('param 1')
            expect(list.$props.parameters[2].name).toBe('param 2')
        });

        it('Test move 2nd parameter down', async function () {
            await clickParamAction('param 2', 'arrow_downward');

            expect(list.$props.parameters[2].name).toBe('param 2')
        });

        it('Test move 2nd parameter down twice', async function () {
            await clickParamAction('param 2', 'arrow_downward');
            await clickParamAction('param 2', 'arrow_downward');

            expect(list.$props.parameters[2].name).toBe('param 2')
        });

        it('Test move 2nd parameter down and then last', async function () {
            await clickParamAction('param 2', 'arrow_downward');
            await clickParamAction('param 3', 'arrow_downward');

            expect(list.$props.parameters[1].name).toBe('param 2')
            expect(list.$props.parameters[2].name).toBe('param 3')
        });

        it('Test move first parameter down twice', async function () {
            await clickParamAction('param 1', 'arrow_downward');
            await clickParamAction('param 1', 'arrow_downward');

            expect(list.$props.parameters[0].name).toBe('param 2')
            expect(list.$props.parameters[1].name).toBe('param 3')
            expect(list.$props.parameters[2].name).toBe('param 1')
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

        it('Test open toast on delete', async function () {
            $(list.$el.parentNode).find('div.toast').remove();

            await clickParamAction('param 2', 'delete');

            const toasts = $(list.$el.parentNode).find('div.toast');

            expect(toasts.length).toBe(1)
            expect(toasts.find('span').text()).toBe('Deleted param 2')
            expect(toasts.find('button').text()).toBe('Undo');
        });

        it('Test open multiple toasts on delete', async function () {
            $(list.$el.parentNode).find('div.toast').remove();

            await clickParamAction('param 2', 'delete');
            await clickParamAction('param 1', 'delete');
            await clickParamAction('param 3', 'delete');

            const toasts = $(list.$el.parentNode).find('div.toast');

            expect(toasts.length).toBe(3)
            expect($(toasts.get(0)).find('span').text()).toBe('Deleted param 2')
            expect($(toasts.get(1)).find('span').text()).toBe('Deleted param 1')
            expect($(toasts.get(2)).find('span').text()).toBe('Deleted param 3')
        });

        it('Test undo button on toast', async function () {
            $(list.$el.parentNode).find('div.toast').remove();

            await clickParamAction('param 2', 'delete');

            const undoButton = $(list.$el.parentNode).find('div.toast button').get(0);
            triggerSingleClick(undoButton);

            await vueTicks();

            expect(findParamItem('param 2')).not.toBeNil()
            expect(list.$props.parameters[0].name).toBe('param 1')
            expect(list.$props.parameters[1].name).toBe('param 2')
            expect(list.$props.parameters[2].name).toBe('param 3')
        });

        it('Test undo button on toast after everything deleted', async function () {
            $(list.$el.parentNode).find('div.toast').remove();

            await clickParamAction('param 2', 'delete');
            await clickParamAction('param 1', 'delete');
            await clickParamAction('param 3', 'delete');

            const undoButton = $(list.$el.parentNode).find('div.toast button').get(0);
            triggerSingleClick(undoButton);

            await vueTicks();

            expect(findParamItem('param 2')).not.toBeNil()
            expect(list.$props.parameters[0].name).toBe('param 2')
        });
    });

    describe('Test edit parameter', function () {

        it('Test set missing value', async function () {
            clickOnParam('param 1');
            assertOpen('param 1');

            await setValue('param 1', 'type', 'int');
            assertOpen('param 1');
            expect(list.$props.parameters[0].type).toBe('int')
        });
    });

    describe('Test add parameter', function () {
        const clickAddButton = () => {
            const addParamButton = $(list.$el).find('li.add-param-item').get(0);
            triggerSingleClick(addParamButton);
        };

        it('Test add parameter', async function () {
            clickAddButton();

            await vueTicks();

            expect(list.$props.parameters.length).toBe(4)
            expect(list.$props.parameters[3].name).toBe(undefined)

            list.openingNewParam = false;
            await timeout(100);
        });

        it('Test add multiple parameters', async function () {
            clickAddButton();
            clickAddButton();
            clickAddButton();

            await vueTicks();

            expect(list.$props.parameters.length).toBe(6)
            expect(list.$props.parameters[3].name).toBe(undefined)
            expect(list.$props.parameters[4].name).toBe(undefined)
            expect(list.$props.parameters[5].name).toBe(undefined)

            list.openingNewParam = false;
            await timeout(100);
        });
    });

});
'use strict';

import ParamListItem from '@/admin/components/scripts-config/ParamListItem';
import ScriptParamList from '@/admin/components/scripts-config/ScriptParamList';
import {hasClass} from '@/common/utils/common';
import {assert, config as chaiConfig} from 'chai';
import {createVue, timeout, triggerSingleClick, vueTicks} from '../test_utils';
import {setValueByUser} from './ParameterConfigForm_test';


chaiConfig.truncateThreshold = 0;

describe('Test ScriptParamList', function () {
    let list;
    let errors;

    beforeEach(async function () {
        errors = [];

        list = createVue(ScriptParamList, {
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
        });
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
        assert.exists(paramItem);

        const index = list.$children.indexOf(paramItem);
        M.Collapsible.getInstance(list.$el).open(index);
    }

    function assertOpen(paramName) {
        let paramItem = findParamItem(paramName);
        assert.exists(paramItem);

        assert.isTrue(hasClass(paramItem.$el, 'active'));
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
        assert.exists(paramItem);

        assert.isFalse(hasClass(paramItem.$el, 'active'));
    }

    async function setValue(paramName, fieldName, value) {
        let paramItem = findParamItem(paramName);
        assert.exists(paramItem);

        const paramForm = paramItem.$children[0];
        await setValueByUser(paramForm, fieldName, value)
    }

    describe('Test visualisation', function () {
        it('Test show parameters list', async function () {
            assert.exists(findParamItem('param 1'));
            assert.exists(findParamItem('param 2'));
            assert.exists(findParamItem('param 3'));
        });

        it('Test show add param button', async function () {
            const button = $(list.$el).find('li.add-param-item').get(0);
            assert.exists(button);
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

            assert.exists(findParamItem('new name'));
        });
    });

    describe('Test move parameters', function () {
        it('Test move 2nd parameter up', async function () {
            await clickParamAction('param 2', 'arrow_upward');

            assert.equal(list.$props.parameters[0].name, 'param 2');
        });

        it('Test move 2nd parameter up twice', async function () {
            await clickParamAction('param 2', 'arrow_upward');
            await clickParamAction('param 2', 'arrow_upward');

            assert.equal(list.$props.parameters[0].name, 'param 2');
        });

        it('Test move 2nd parameter up and then first', async function () {
            await clickParamAction('param 2', 'arrow_upward');
            await clickParamAction('param 1', 'arrow_upward');

            assert.equal(list.$props.parameters[0].name, 'param 1');
            assert.equal(list.$props.parameters[1].name, 'param 2');
        });

        it('Test move 3rd parameter up twice', async function () {
            await clickParamAction('param 3', 'arrow_upward');
            await clickParamAction('param 3', 'arrow_upward');

            assert.equal(list.$props.parameters[0].name, 'param 3');
            assert.equal(list.$props.parameters[1].name, 'param 1');
            assert.equal(list.$props.parameters[2].name, 'param 2');
        });

        it('Test move 2nd parameter down', async function () {
            await clickParamAction('param 2', 'arrow_downward');

            assert.equal(list.$props.parameters[2].name, 'param 2');
        });

        it('Test move 2nd parameter down twice', async function () {
            await clickParamAction('param 2', 'arrow_downward');
            await clickParamAction('param 2', 'arrow_downward');

            assert.equal(list.$props.parameters[2].name, 'param 2');
        });

        it('Test move 2nd parameter down and then last', async function () {
            await clickParamAction('param 2', 'arrow_downward');
            await clickParamAction('param 3', 'arrow_downward');

            assert.equal(list.$props.parameters[1].name, 'param 2');
            assert.equal(list.$props.parameters[2].name, 'param 3');
        });

        it('Test move first parameter down twice', async function () {
            await clickParamAction('param 1', 'arrow_downward');
            await clickParamAction('param 1', 'arrow_downward');

            assert.equal(list.$props.parameters[0].name, 'param 2');
            assert.equal(list.$props.parameters[1].name, 'param 3');
            assert.equal(list.$props.parameters[2].name, 'param 1');
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

            assert.notExists(findParamItem('param 1'));
            assert.exists(findParamItem('param 2'));
            assert.exists(findParamItem('param 3'));
        });

        it('Test delete parameter in the middle', async function () {
            await clickParamAction('param 2', 'delete');

            assert.exists(findParamItem('param 1'));
            assert.notExists(findParamItem('param 2'));
            assert.exists(findParamItem('param 3'));
        });

        it('Test delete parameter in the end', async function () {
            await clickParamAction('param 3', 'delete');

            assert.exists(findParamItem('param 1'));
            assert.exists(findParamItem('param 2'));
            assert.notExists(findParamItem('param 3'));
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

            assert.equal(toasts.length, 1);
            assert.equal(toasts.find('span').text(), 'Deleted param 2');
            assert.equal(toasts.find('button').text(), 'Undo');
        });

        it('Test open multiple toasts on delete', async function () {
            $(list.$el.parentNode).find('div.toast').remove();

            await clickParamAction('param 2', 'delete');
            await clickParamAction('param 1', 'delete');
            await clickParamAction('param 3', 'delete');

            const toasts = $(list.$el.parentNode).find('div.toast');

            assert.equal(toasts.length, 3);
            assert.equal($(toasts.get(0)).find('span').text(), 'Deleted param 2');
            assert.equal($(toasts.get(1)).find('span').text(), 'Deleted param 1');
            assert.equal($(toasts.get(2)).find('span').text(), 'Deleted param 3');
        });

        it('Test undo button on toast', async function () {
            $(list.$el.parentNode).find('div.toast').remove();

            await clickParamAction('param 2', 'delete');

            const undoButton = $(list.$el.parentNode).find('div.toast button').get(0);
            triggerSingleClick(undoButton);

            await vueTicks();

            assert.exists(findParamItem('param 2'));
            assert.equal(list.$props.parameters[0].name, 'param 1');
            assert.equal(list.$props.parameters[1].name, 'param 2');
            assert.equal(list.$props.parameters[2].name, 'param 3');
        });

        it('Test undo button on toast after everything deleted', async function () {
            $(list.$el.parentNode).find('div.toast').remove();

            await clickParamAction('param 2', 'delete');
            await clickParamAction('param 1', 'delete');
            await clickParamAction('param 3', 'delete');

            const undoButton = $(list.$el.parentNode).find('div.toast button').get(0);
            triggerSingleClick(undoButton);

            await vueTicks();

            assert.exists(findParamItem('param 2'));
            assert.equal(list.$props.parameters[0].name, 'param 2');
        });
    });

    describe('Test edit parameter', function () {

        it('Test set missing value', async function () {
            clickOnParam('param 1');
            assertOpen('param 1');

            await setValue('param 1', 'type', 'int');
            assertOpen('param 1');
            assert.equal(list.$props.parameters[0].type, 'int');
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

            assert.equal(list.$props.parameters.length, 4);
            assert.equal(list.$props.parameters[3].name, undefined);

            list.openingNewParam = false;
            await timeout(100);
        });

        it('Test add multiple parameters', async function () {
            clickAddButton();
            clickAddButton();
            clickAddButton();

            await vueTicks();

            assert.equal(list.$props.parameters.length, 6);
            assert.equal(list.$props.parameters[3].name, undefined);
            assert.equal(list.$props.parameters[4].name, undefined);
            assert.equal(list.$props.parameters[5].name, undefined);

            list.openingNewParam = false;
            await timeout(100);
        });
    });

});
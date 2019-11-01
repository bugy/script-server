'use strict';

import {mount} from '@vue/test-utils';
import {assert, config as chaiConfig} from 'chai';
import ParamListItem from '../../js/admin/scripts-config/ParamListItem';
import ScriptParamList from '../../js/admin/scripts-config/ScriptParamList';
import {hasClass} from '../../js/common';
import {vueTicks} from '../test_utils';
import {setValueByUser} from './ParameterConfigForm_test';

chaiConfig.truncateThreshold = 0;

describe('Test ScriptParamList', function () {
    let list;
    let errors;

    beforeEach(async function () {
        errors = [];

        list = mount(ScriptParamList, {
            attachToDocument: true,
            sync: false,
            propsData: {
                parameters: [
                    {
                        'name': 'param 1',
                        'description': 'some description'
                    },
                    {
                        'name': 'param 2'
                    }]
            }
        });
        list.vm.$parent.$forceUpdate();
        await list.vm.$nextTick();
    });

    afterEach(async function () {
        await vueTicks();

        list.destroy();
    });

    function findParamItem(paramName) {
        let foundChild = null;
        for (const child of list.vm.$children) {
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
        assert.isNotNull(paramItem);

        const index = list.vm.$children.indexOf(paramItem);
        M.Collapsible.getInstance(list.vm.$el).open(index);
    }

    function assertOpen(paramName) {
        let paramItem = findParamItem(paramName);
        assert.isNotNull(paramItem);

        assert.isTrue(hasClass(paramItem.$el, 'active'));
    }

    async function setValue(paramName, fieldName, value) {
        let paramItem = findParamItem(paramName);
        assert.isNotNull(paramItem);

        const paramForm = paramItem.$children[0];
        await setValueByUser(paramForm, fieldName, value)
    }

    describe('Test edit parameter', function () {

        it('Test set missing value', async function () {
            clickOnParam('param 1');
            assertOpen('param 1');

            await setValue('param 1', 'type', 'int');
            assertOpen('param 1');
            assert.equal(list.vm.$props.parameters[0].type, 'int');
        });
    });

});
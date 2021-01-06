import {forEachKeyValue} from '@/common/utils/common';
import Vue from 'vue';
import {createLocalVue} from '@vue/test-utils'
import vueDirectives from '@/common/vueDirectives'

export async function vueTicks(count = 3) {
    if (count === 0) {
        return Promise.resolve(null);
    }

    let promise = Vue.nextTick();
    for (let i = 0; i < (count - 1); i++) {
        promise.then(function () {
            return Vue.nextTick();
        });
    }
    return promise;
}

export async function timeout(ms) {
    return new Promise((resolve, reject) => {
        setTimeout(resolve, ms);
    });
}

export function wrapVModel(inputComponent) {
    inputComponent.vm.$on('input', function (value) {
        inputComponent.setProps({value});
    });
    inputComponent.vm.$on('error', error => inputComponent.currentError = error);
}

export function setDeepProp(wrapper, key, value) {
    const keys = key.split('.');

    if (keys.length === 1) {
        wrapper.setProps({[key]: value})
    }

    const rootKey = keys[0];
    const newRootElement = Object.assign({}, wrapper.props(rootKey));

    let currentElement = newRootElement;
    for (let i = 1; i < keys.length - 1; i++) {
        const key = keys[i];
        currentElement = currentElement[key];
    }

    if (currentElement[keys[keys.length - 1]] !== value) {
        currentElement[keys[keys.length - 1]] = value;
        wrapper.setProps({[rootKey]: newRootElement})
    }
}

export function triggerDoubleClick(element) {
    const event = new MouseEvent('dblclick', {'relatedTarget': element});
    element.dispatchEvent(event);
}

export function triggerSingleClick(element) {
    const event = new MouseEvent('click', {'relatedTarget': element});
    element.dispatchEvent(event);
}

export function triggerKeyEvent(element, type, code) {
    const event = new KeyboardEvent(type, {key: code, keyCode: code, which: code});
    element.dispatchEvent(event);
}

export function setChipListValue(chipListComponent, value) {
    const chipList = M.Chips.getInstance($(chipListComponent.$el).find('.chips').get(0));
    while (chipList.chipsData.length > 0) {
        chipList.deleteChip(0);
    }
    for (const valueElement of value) {
        chipList.addChip({'tag': valueElement});
    }
}

export function createVue(component, properties, store = null) {
    document.body.insertAdjacentHTML('afterbegin', '<div id="top-level-element"></div>');
    const topLevelElement = document.getElementById('top-level-element');

    const ComponentClass = Vue.extend(component);
    const vm = new ComponentClass({
        store,
        propsData: properties
    }).$mount(topLevelElement);

    vm.$on('input', function (value) {
        vm.value = value
    });

    return vm;
}

export function destroy(component) {
    component.destroy();
}

export const flushPromises = () => new Promise(resolve => setTimeout(resolve));

export const createScriptServerTestVue = () => {
    const vue = createLocalVue()
    forEachKeyValue(vueDirectives, (id, definition) => {
        vue.directive(id, definition)
    })
    return vue
}
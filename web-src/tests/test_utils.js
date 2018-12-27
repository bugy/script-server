import Vue from 'vue';
import {isNull} from '../js/common';

export async function vueTicks(count) {
    if (isNull(count)) {
        count = 3;
    } else if (count === 0) {
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
    const newRootElement = $.extend(true, {}, wrapper.props(rootKey));

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

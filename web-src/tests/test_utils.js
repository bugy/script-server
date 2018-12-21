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
        inputComponent.vm.value = value;
    });
    inputComponent.vm.$on('error', error => inputComponent.currentError = error);
}
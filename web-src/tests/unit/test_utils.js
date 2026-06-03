import {nextTick} from 'vue';
import {mount} from '@vue/test-utils';

export async function vueTicks(count = 3) {
    if (count === 0) {
        return Promise.resolve(null);
    }

    let promise = nextTick();
    for (let i = 0; i < (count - 1); i++) {
        promise = promise.then(() => nextTick());
    }
    return promise;
}

export async function timeout(ms) {
    return new Promise((resolve, reject) => {
        setTimeout(resolve, ms);
    });
}

// Vue 3 removed instance `$on`. To emulate parent v-model two-way binding in
// tests, we register `onUpdate:modelValue` / `onError` listeners as props after
// mount: when the component emits, we push the value back into its `modelValue`
// prop (mirroring what a parent `v-model` would do) and capture errors.
export function wrapVModel(inputComponent) {
    inputComponent.setProps({
        'onUpdate:modelValue': (value) => inputComponent.setProps({modelValue: value}),
        'onError': (error) => {
            inputComponent.currentError = error
        }
    });
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

export function triggerFocusEvent(element) {
    const event = new Event('focus', {bubbles: true, cancelable: true});
    element.dispatchEvent(event);
}

export function focus(element) {
    const prevFocus = document.activeElement
    if (prevFocus === element) {
        return
    }

    element.focus()
    triggerFocusEvent(element)

    if (prevFocus) {
        const blurEvent = new Event('blur', {bubbles: true, cancelable: true});
        prevFocus.dispatchEvent(blurEvent);
    }
}

export function setChipListValue(chipListComponent, value) {
    const chipList = M.Chips.getInstance(chipListComponent.$el.querySelector('.chips'));
    while (chipList.chipsData.length > 0) {
        chipList.deleteChip(0);
    }
    for (const valueElement of value) {
        chipList.addChip({'tag': valueElement});
    }
}

// Vue 3 / VTU v2 replacement for the old `new ComponentClass().$mount()` helper.
// Returns a VTU wrapper (callers use wrapper.vm, wrapper.unmount(), etc.).
export function createVue(component, properties, store = null) {
    return mount(component, {
        attachTo: attachToDocument(),
        props: properties,
        global: store ? {plugins: [store]} : {}
    });
}

export function destroy(wrapper) {
    wrapper.unmount();
}

export const flushPromises = () => new Promise(resolve => setTimeout(resolve));

// Deprecated no-op kept for backward compatibility: in Vue 3 / VTU v2 there is no
// `createLocalVue`. The app's directives are registered globally in setup.js via
// `config.global.directives`, so the old `localVue` mount option is unnecessary.
export const createScriptServerTestVue = () => undefined;

export const attachToDocument = () => {
    const element = document.createElement('div')
    document.body.appendChild(element)
    return element
}

export const mapArrayWrapper = (arrayWrapper, mapFunction) => {
    const result = []

    for (let i = 0; i < arrayWrapper.length; i++) {
        const element = arrayWrapper.at(i)

        result.push(mapFunction(element))
    }

    return result
}

export const awaitVisible = async (element, maxTimeout) => {
    for (let awaited = 0; awaited < maxTimeout; awaited += 10) {
        await timeout(10)

        const style = window.getComputedStyle(element)
        if ((style.opacity > 0) && (style.display !== 'none')) {
            break
        }
    }

    expect(element).toBeVisible()
}

export const awaitInvisible = async (element, maxTimeout) => {
    for (let awaited = 0; awaited < maxTimeout; awaited += 10) {
        await timeout(10)

        const style = window.getComputedStyle(element)
        if ((style.opacity === '0') || (style.display === 'none')) {
            break
        }
    }

    expect(element).not.toBeVisible()
}

export function getNodeText(element) {
    return Array.from(element.childNodes)
        .filter(child => child.nodeType === 3)
        .map(child => child.nodeValue.trim())
        .reduce((left, right) => left + right);
}
async function vueTicks(count) {
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

function createVue(componentName, properties) {
    document.body.insertAdjacentHTML('afterbegin', '<div id="top-level-element"></div>');
    const topLevelElement = document.getElementById('top-level-element');

    let componentConstructor = Vue.options.components[componentName];

    const vm = new componentConstructor({
        propsData: properties
    }).$mount(topLevelElement);

    vm.$on('input', function (value) {
        vm.value = value
    });

    return vm;
}

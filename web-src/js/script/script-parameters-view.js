'use strict';

(function () {

    //noinspection JSAnnotator
    Vue.component('script-parameters-view', {
        template:
            '<div class="script-parameters-panel">\n'
            + '        <template v-for="parameter in parametersState.parameters">\n'
            + '            <component '
            + '             :is="getComponentType(parameter)" '
            + '             :config="parameter"'
            + '             v-model="parametersState.parameterValues[parameter.name]" '
            + '             :key="parameter.name"'
            + '             class="inline parameter"'
            + '             @error="handleError(parameter, $event)"/>'
            + '        </template>\n'
            + '</div>',

        props: {
            parametersState: Object
        },

        data() {
            return {
                errors: {}
            }
        },

        methods: {
            getComponentType(parameter) {
                if (parameter.withoutValue) {
                    return 'checkbox';
                } else if ((parameter.type === 'list') || (parameter.type === 'multiselect')) {
                    return 'combobox';
                } else if (parameter.type === 'file_upload') {
                    return 'file-upload-field';
                } else {
                    return 'textfield';
                }
            },

            handleError(parameter, error) {
                if (isEmptyString(error)) {
                    delete this.errors[parameter.name];
                } else {
                    this.errors[parameter.name] = error;
                }
            },

            getErrors() {
                return this.errors;
            }
        }
    });
}());

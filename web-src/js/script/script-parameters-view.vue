<template>
    <div class="script-parameters-panel">
        <template v-for="parameter in parameters">
            <component
                    :is="getComponentType(parameter)"
                    :config="parameter"
                    :value="parameterValues[parameter.name]"
                    :key="parameter.name"
                    class="inline parameter"
                    @input="setParameterValue(parameter.name, $event)"
                    @error="handleError(parameter, $event)"/>
        </template>
    </div>
</template>

<script>
    import {mapState} from 'vuex'
    import {isEmptyString} from '../common';
    import Checkbox from '../components/checkbox'
    import Combobox from '../components/combobox'
    import FileUpload from '../components/file_upload'
    import ServerFileField from '../components/server_file_field'
    import Textfield from '../components/textfield'
    import {comboboxTypes} from './model_helper'
    import {isRecursiveFileParameter} from './model_helper';
    import {SET_PARAMETER_VALUE} from './vuex_constants';

    export default {
        name: 'script-parameters-view',

        data() {
            return {
                errors: {}
            }
        },

        computed: {
            ...mapState({
                parameters: 'parameters',
                parameterValues: 'parameterValues'
            })
        },

        methods: {
            getComponentType(parameter) {
                if (parameter.withoutValue) {
                    return Checkbox;
                } else if (isRecursiveFileParameter(parameter)) {
                    return ServerFileField;
                } else if (comboboxTypes.includes(parameter.type)) {
                    return Combobox;
                } else if (parameter.type === 'file_upload') {
                    return FileUpload;
                } else {
                    return Textfield;
                }
            },

            handleError(parameter, error) {
                if (isEmptyString(error)) {
                    delete this.errors[parameter.name];
                } else {
                    this.errors[parameter.name] = error;
                }
            },

            setParameterValue(parameterName, value) {
                const errorMessage = this.errors[parameterName];
                this.$store.commit(SET_PARAMETER_VALUE, {parameterName, value, errorMessage});
            },

            getErrors() {
                return this.errors;
            }
        }
    }
</script>

<style scoped>

</style>

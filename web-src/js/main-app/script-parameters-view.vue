<template>
    <div class="script-parameters-panel">
        <template v-for="parameter in parameters">
            <component
                    :config="parameter"
                    :is="getComponentType(parameter)"
                    :key="parameter.name"
                    :value="parameterValues[parameter.name]"
                    @error="handleError(parameter, $event)"
                    @input="setParameterValue(parameter.name, $event)"
                    class="inline parameter"/>
        </template>
    </div>
</template>

<script>
    import {mapActions, mapState} from 'vuex'
    import Checkbox from '../components/checkbox'
    import Combobox from '../components/combobox'
    import FileUpload from '../components/file_upload'
    import ServerFileField from '../components/server_file_field'
    import Textfield from '../components/textfield'
    import {comboboxTypes, isRecursiveFileParameter} from './model_helper'

    export default {
        name: 'script-parameters-view',

        computed: {
            ...mapState('scriptConfig', {
                parameters: 'parameters'
            }),
            ...mapState('scriptSetup', {
                parameterValues: 'parameterValues'
            })
        },

        methods: {
            ...mapActions('scriptSetup', {
                setParameterValueInStore: 'setParameterValue',
                setParameterErrorInStore: 'setParameterError'
            }),
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
                this.setParameterErrorInStore({parameterName: parameter.name, errorMessage: error})
            },

            setParameterValue(parameterName, value) {
                this.setParameterValueInStore({parameterName, value});
            }
        }
    }
</script>

<style scoped>
    .script-parameters-panel >>> {
        margin-top: 15px;
        margin-right: 24px;
        display: flex;
        flex-wrap: wrap;
    }

    .script-parameters-panel >>> .parameter {
        margin: 7px 0 20px 24px;

        flex-grow: 1;
        flex-shrink: 0;
        flex-basis: 180px;
        max-width: 220px;
    }

    .script-parameters-panel >>> .parameter input {
        margin: 0;

        font-size: 1rem;
        height: 1.5em;
        line-height: 1.5em;
    }

    .script-parameters-panel >>> .parameter > label {
        transform: none;
        font-size: 1rem;
    }

    .script-parameters-panel >>> .parameter > label.active {
        transform: translateY(-70%) scale(0.8);
    }

    .script-parameters-panel >>> .input-field input[type=checkbox] + span {
        padding-left: 28px;
    }

    .script-parameters-panel >>> input[type="text"]:invalid,
    .script-parameters-panel >>> input[type="number"]:invalid {
        border-bottom: 1px solid #e51c23;
        box-shadow: 0 1px 0 0 #e51c23;
    }

    .script-parameters-panel >>> .input-field:after {
        content: attr(data-error);
        color: #F44336;
        font-size: 0.9rem;
        display: block;
        position: absolute;
        top: 23px;
        left: 0.75rem;
    }

    .script-parameters-panel >>> .input-field .select-wrapper + label {
        transform: scale(0.8);
        top: -18px;
    }

    .script-parameters-panel >>> .dropdown-content {
        max-width: 50vw;
        min-width: 100%;
        white-space: nowrap;

        margin-bottom: 0;
    }

    .script-parameters-panel >>> .dropdown-content > li > span {
        overflow-x: hidden;
        text-overflow: ellipsis;
    }

</style>

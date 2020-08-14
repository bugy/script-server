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
    import Checkbox from '@/common/components/checkbox'
    import Combobox from '@/common/components/combobox'
    import FileUpload from '@/common/components/file_upload'
    import ServerFileField from '@/common/components/server_file_field'
    import Textfield from '@/common/components/textfield'
    import {mapActions, mapState} from 'vuex'
    import {comboboxTypes, isRecursiveFileParameter} from '../../utils/model_helper'

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
        margin-right: 0;
        display: flex;
        flex-wrap: wrap;
    }

    .script-parameters-panel >>> .parameter {
        margin: 7px 24px 20px 0;

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

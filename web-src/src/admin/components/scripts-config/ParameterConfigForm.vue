<template>
    <form class="parameter-config-form col">
        <div class="row">
            <Textfield :config="nameField" @error="handleError(nameField, $event)" class="col s4" v-model="name"/>
            <Checkbox :config="requiredField" @error="handleError(requiredField, $event)" class="col s3 offset-s1"
                      v-model="required"/>
            <Checkbox :config="secureField" @error="handleError(secureField, $event)" class="col s3" v-model="secure"/>
        </div>
        <div class="row">
            <Textfield :config="argField" @error="handleError(argField, $event)" class="col s4" v-model="arg"/>
            <Checkbox :config="noValueField" @error="handleError(noValueField, $event)" class="col s3 offset-s1"
                      v-model="noValue"/>
            <Combobox :config="typeField" :disabled="noValue || constant" :dropdownContainer="this.$el"
                      @error="handleError(typeField, $event)"
                      class="col s4" v-model="type"/>
        </div>
        <div class="row">
            <Textfield :config="envVarField" @error="handleError(envVarField, $event)" class="col s4" v-model="envVar"/>
            <Checkbox :config="paramSpaceField" @error="handleError(paramSpaceField, $event)" class="col s3 offset-s1"
                      v-model="paramSpace" v-if="!noValue" />
        </div>
        <div class="row" v-if="selectedType !== 'file_upload' && !noValue">
            <Textfield :class="{s6: !isExtendedDefault, s8: isExtendedDefault}" :config="defaultValueField"
                       @error="handleError(defaultValueField, $event)" class="col"
                       v-model="defaultValue"/>
            <Checkbox :config="constantField" @error="handleError(constantField, $event)" class="col s3 offset-s1"
                      v-model="constant"/>
        </div>
        <div class="row" v-if="!constant">
            <TextArea :config="descriptionField" @error="handleError(descriptionField, $event)" class="col s12"
                      v-model="description"/>
        </div>
        <div class="row" v-if="selectedType === 'int'">
            <Textfield :config="minField" @error="handleError(minField, $event)" class="col s5" v-model="min"/>
            <Textfield :config="maxField" @error="handleError(maxField, $event)" class="col s6 offset-s1"
                       v-model="max"/>
        </div>
        <div class="row" v-if="(selectedType === 'list' || selectedType === 'multiselect')">
            <Textfield :config="allowedValuesScriptField" @error="handleError(allowedValuesScriptField, $event)"
                       class="col s9"
                       v-if="allowedValuesFromScript" v-model="allowedValuesScript"/>
            <ChipsList @error="handleError('Allowed values', $event)" class="col s9" title="Allowed values" v-else
                       v-model="allowedValues"/>
            <Checkbox :config="allowedValuesFromScriptField" @error="handleError(allowedValuesFromScriptField, $event)"
                      class="col s3"
                      v-model="allowedValuesFromScript"/>
        </div>
        <div class="row" v-if="(selectedType === 'multiselect')">
            <Checkbox :config="multipleArgumentsField" @error="handleError(multipleArgumentsField, $event)"
                      class="col s4"
                      v-model="multipleArguments"/>
            <Checkbox :config="repeatArgField" @error="handleError(repeatArgField, $event)"
                      class="col s3" v-if="multipleArguments"
                      v-model="repeatArg"/>
            <Textfield :config="separatorField" v-if="!multipleArguments"
                       @error="handleError(separatorField, $event)" class="col s3"
                       v-model="separator"/>
        </div>
        <div class="row" v-if="(selectedType === 'server_file')">
            <Textfield :config="fileDirField" @error="handleError(fileDirField, $event)" class="col s5"
                       v-model="fileDir"/>
            <Checkbox :config="recursiveField" @error="handleError(recursiveField, $event)" class="col s2 offset-s1"
                      v-model="recursive"/>
            <Combobox :config="fileTypeField" @error="handleError(fileTypeField, $event)" class="col s3 offset-s1"
                      v-model="fileType"/>
            <ChipsList @error="handleError('Allowed file extensions', $event)" class="col s12"
                       title="Allowed file extensions"
                       v-model="fileExtensions"/>
        </div>
    </form>
</template>

<script>
    import Checkbox from '@/common/components/checkbox';
    import ChipsList from '@/common/components/ChipsList';
    import Combobox from '@/common/components/combobox';
    import TextArea from '@/common/components/TextArea';
    import Textfield from '@/common/components/textfield';
    import {forEachKeyValue, isEmptyString} from '@/common/utils/common';
    import get from 'lodash/get';
    import Vue from 'vue';
    import {
        allowedValuesFromScriptField,
        allowedValuesScriptField,
        argField,
        paramSpaceField,
        constantField,
        defaultValueField,
        descriptionField,
        envVarField,
        fileDirField,
        fileTypeField,
        maxField,
        minField,
        multipleArgumentsField,
        repeatArgField,
        nameField,
        noValueField,
        recursiveField,
        requiredField,
        secureField,
        separatorField,
        typeField
    } from './parameter-fields';

    function updateValue(value, configField, newValue) {
        if (!value.hasOwnProperty(configField)) {
            Object.assign(value, {[configField]: newValue});
        }
        Vue.set(value, configField, newValue);
    }

    export default {
        name: 'ParameterConfigForm',
        components: {ChipsList, TextArea, Checkbox, Combobox, Textfield},
        props: {
            value: {
                type: Object,
                default: null
            }
        },

        mounted: function () {
            const simpleFields = {
                name: 'name',
                description: 'description',
                arg: 'param',
                paramSpace: 'param_space',
                envVar: 'env_var',
                type: 'type',
                noValue: 'no_value',
                required: 'required',
                constant: 'constant',
                secure: 'secure',
                min: 'min',
                max: 'max',
                multipleArguments: 'multiple_arguments',
                repeatArg: 'repeat_arg',
                separator: 'separator',
                fileDir: 'file_dir',
                recursive: 'file_recursive',
                fileType: 'file_type'
            };

            forEachKeyValue(simpleFields, (vmField, configField) => {
                this.$watch(vmField, (newValue) => updateValue(this.value, configField, newValue));
            });

            for (const child of this.$children) {
                let fieldName;
                if (child.$options._componentTag === ChipsList.name) {
                    fieldName = child.title;
                } else {
                    fieldName = child.$props.config.name;
                }
            }
        },


        data() {
            return {
                name: null,
                arg: null,
                paramSpace: null,
                envVar: null,
                type: null,
                noValue: null,
                required: null,
                description: null,
                min: null,
                max: null,
                allowedValues: null,
                allowedValuesScript: null,
                allowedValuesFromScript: null,
                defaultValue: null,
                constant: null,
                secure: null,
                multipleArguments: null,
                repeatArg: null,
                separator: null,
                fileDir: null,
                recursive: null,
                fileType: null,
                fileExtensions: null,
                nameField,
                argField: Object.assign({}, argField),
                paramSpaceField,
                envVarField,
                typeField,
                noValueField,
                requiredField,
                secureField,
                descriptionField,
                minField,
                maxField: Object.assign({}, maxField),
                allowedValuesScriptField,
                allowedValuesFromScriptField,
                defaultValueField: Object.assign({}, defaultValueField),
                constantField,
                multipleArgumentsField,
                repeatArgField,
                separatorField,
                fileDirField,
                recursiveField,
                fileTypeField
            }
        },

        watch: {
            value: {
                immediate: true,
                handler(config) {
                    if (config) {
                        this.name = config['name'];
                        this.description = config['description'];
                        this.arg = config['param'];
                        this.paramSpace = !!get(config, 'param_space', true);
                        this.envVar = config['env_var'];
                        this.type = config['type'];
                        this.noValue = get(config, 'no_value', false);
                        this.required = get(config, 'required', false);
                        this.min = config['min'];
                        this.max = config['max'];
                        this.constant = !!get(config, 'constant', false);
                        this.secure = !!get(config, 'secure', false);
                        this.multipleArguments = !!get(config, 'multiple_arguments', false);
                        this.repeatArg = !!get(config, 'repeat_arg', false);
                        this.separator = get(config, 'separator', ',');
                        this.fileDir = config['file_dir'];
                        this.recursive = !!get(config, 'file_recursive', false);
                        this.fileType = get(config, 'file_type', 'any');
                        this.fileExtensions = get(config, 'file_extensions', []);

                        const defaultValue = get(config, 'default', '');
                        if (this.isRecursiveFile()) {
                            if (Array.isArray(defaultValue)) {
                                this.defaultValue = defaultValue.join('/');
                                if (this.defaultValue.startsWith('//')) {
                                    this.defaultValue = this.defaultValue.substring(1);
                                }

                            } else {
                                this.defaultValue = defaultValue;
                            }
                        } else {
                            this.defaultValue = defaultValue.toString();
                        }

                        const allowedValues = get(config, 'values', []);
                        if (Array.isArray(allowedValues) || !allowedValues['script']) {
                            this.allowedValues = allowedValues;
                            this.allowedValuesFromScript = false;
                            this.allowedValuesScript = '';
                        } else {
                            this.allowedValues = [];
                            this.allowedValuesFromScript = true;
                            this.allowedValuesScript = allowedValues['script'];
                        }
                    }
                }
            },
            noValue: {
                immediate: true,
                handler(noValue) {
                    Vue.set(this.argField, 'required', noValue);
                }
            },
            constant: {
                immediate: true,
                handler(constant) {
                    Vue.set(this.defaultValueField, 'required', constant);
                    Vue.set(this.defaultValueField, 'name', constant ? 'Constant value' : defaultValueField.name);
                }
            },
            min: {
                handler(min) {
                    Vue.set(this.maxField, 'min', min);
                }
            },
            fileExtensions(fileExtensions) {
                updateValue(this.value, 'file_extensions', fileExtensions);
            },
            allowedValuesFromScript() {
                this.updateAllowedValues();
            },
            allowedValues() {
                this.updateAllowedValues();
            },
            allowedValuesScript() {
                this.updateAllowedValues();
            },
            defaultValue() {
                if (this.selectedType === 'multiselect') {
                    updateValue(this.value, 'default', this.defaultValue.split(',').filter(s => !isEmptyString(s)));
                } else if (this.isRecursiveFile()) {
                    let path = this.defaultValue.split('/').filter(s => !isEmptyString(s));
                    if (this.defaultValue.startsWith('/')) {
                        path = ['/', ...path];
                    }
                    updateValue(this.value, 'default', path);
                } else {
                    updateValue(this.value, 'default', this.defaultValue);
                }
            }
        },

        computed: {
            selectedType() {
                if (this.noValue || this.constant) {
                    return null;
                }

                return this.type;
            },
            isExtendedDefault() {
                return (this.selectedType === 'multiselect') || (this.isRecursiveFile());
            }
        },


        methods: {
            updateAllowedValues() {
                if (this.allowedValuesFromScript) {
                    updateValue(this.value, 'values', {script: this.allowedValuesScript});
                } else {
                    updateValue(this.value, 'values', this.allowedValues);
                }
            },
            isRecursiveFile() {
                return (this.selectedType === 'server_file') && (this.recursive);
            },
            handleError(fieldConfig, error) {
                let fieldName;
                if (fieldConfig instanceof String) {
                    fieldName = fieldConfig;
                } else {
                    fieldName = fieldConfig.name;
                }
                this.$emit('error', {fieldName, message: error});
            }
        }
    }
</script>

<style scoped>
    .parameter-config-form >>> .col.checkbox {
        margin-top: 2.1em;
    }

    .parameter-config-form >>> .row {
        margin-bottom: 0;
    }
</style>
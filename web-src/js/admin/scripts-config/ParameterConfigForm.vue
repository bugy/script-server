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
        <div class="row" v-if="selectedType !== 'file_upload'">
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
            <Textfield :config="separatorField" :disabled="multipleArguments"
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
    import Vue from 'vue';
    import {forEachKeyValue, isEmptyArray, isEmptyString} from '../../common';
    import Checkbox from '../../components/checkbox';
    import Combobox from '../../components/combobox';
    import TextArea from '../../components/TextArea';
    import Textfield from '../../components/textfield';
    import ChipsList from '../components/ChipsList';
    import {
        allowedValuesFromScriptField,
        allowedValuesScriptField,
        argField,
        constantField,
        defaultValueField,
        descriptionField,
        fileDirField,
        fileTypeField,
        maxField,
        minField,
        multipleArgumentsField,
        nameField,
        noValueField,
        recursiveField,
        requiredField,
        secureField,
        separatorField,
        typeField
    } from './parameter-fields';

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
                type: 'type',
                noValue: 'no_value',
                required: 'required',
                constant: 'constant',
                secure: 'secure',
                min: 'min',
                max: 'max',
                multipleArguments: 'multiple_arguments',
                separator: 'separator',
                fileDir: 'file_dir',
                recursive: 'file_recursive',
                fileType: 'file_type'
            };

            forEachKeyValue(simpleFields, (vmField, configField) => {
                this.$watch(vmField, (newValue) => Vue.set(this.value, configField, newValue));
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
                separator: null,
                fileDir: null,
                recursive: null,
                fileType: null,
                fileExtensions: null,
                nameField,
                argField: $.extend({}, argField),
                typeField,
                noValueField,
                requiredField,
                secureField,
                descriptionField,
                minField,
                maxField: $.extend({}, maxField),
                allowedValuesScriptField,
                allowedValuesFromScriptField,
                defaultValueField: $.extend({}, defaultValueField),
                constantField,
                multipleArgumentsField,
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
                        this.type = config['type'];
                        this.noValue = _.get(config, 'no_value', false);
                        this.required = _.get(config, 'required', false);
                        this.min = config['min'];
                        this.max = config['max'];
                        this.constant = !!_.get(config, 'constant', false);
                        this.secure = !!_.get(config, 'secure', false);
                        this.multipleArguments = !!_.get(config, 'multiple_arguments', false);
                        this.separator = _.get(config, 'separator', ',');
                        this.fileDir = config['file_dir'];
                        this.recursive = !!_.get(config, 'file_recursive', false);
                        this.fileType = _.get(config, 'file_type', 'any');
                        this.fileExtensions = _.get(config, 'file_extensions', []);

                        const defaultValue = _.get(config, 'default', '');
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

                        const allowedValues = _.get(config, 'values', []);
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
                if (isEmptyArray(fileExtensions)) {
                    Vue.delete(this.value, 'file_extensions');
                } else {
                    Vue.set(this.value, 'file_extensions', fileExtensions);
                }
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
                    Vue.set(this.value, 'default', this.defaultValue.split(',').filter(s => !isEmptyString(s)));
                } else if (this.isRecursiveFile()) {
                    let path = this.defaultValue.split('/').filter(s => !isEmptyString(s));
                    if (this.defaultValue.startsWith('/')) {
                        path = ['/', ...path];
                    }
                    Vue.set(this.value, 'default', path);
                } else {
                    Vue.set(this.value, 'default', this.defaultValue);
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
                    Vue.set(this.value, 'values', {script: this.allowedValuesScript});
                } else {
                    Vue.set(this.value, 'values', this.allowedValues);
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
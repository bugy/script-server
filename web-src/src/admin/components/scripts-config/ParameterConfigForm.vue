<template>
  <form class="parameter-config-form col">
    <div class="row">
      <Textfield v-model="name" :config="nameField" class="col s4" @error="handleError(nameField, $event)"/>
      <Checkbox v-model="required" :config="requiredField" class="col s3 offset-s1"
                @error="handleError(requiredField, $event)"/>
      <Checkbox v-model="secure" :config="secureField" class="col s3" @error="handleError(secureField, $event)"/>
    </div>
    <div class="row">
      <Textfield v-model="arg" :config="argField" class="col s4" @error="handleError(argField, $event)"/>
      <Checkbox v-model="noValue" :config="noValueField" class="col s3 offset-s1"
                @error="handleError(noValueField, $event)"/>
      <Combobox v-model="type" :config="typeField" :disabled="noValue || constant"
                :dropdownContainer="this.$el"
                class="col s4" @error="handleError(typeField, $event)"/>
    </div>
    <div class="row">
      <Textfield v-model="envVar" :config="envVarField" class="col s4" @error="handleError(envVarField, $event)"/>
      <Checkbox v-if="!noValue" v-model="repeatParam" :config="repeatParamField"
                class="col s3 offset-s1" @error="handleError(repeatParamField, $event)"/>
    </div>
    <div v-if="selectedType !== 'file_upload' && !noValue" class="row">
      <Textfield v-model="defaultValue" :class="{s6: !isExtendedDefault, s8: isExtendedDefault}"
                 :config="defaultValueField" class="col"
                 @error="handleError(defaultValueField, $event)"/>
      <Checkbox v-model="constant" :config="constantField" class="col s3 offset-s1"
                @error="handleError(constantField, $event)"/>
    </div>
    <div v-if="!constant" class="row">
            <TextArea :config="descriptionField" @error="handleError(descriptionField, $event)" class="col s12"
                      v-model="description"/>
    </div>
    <div v-if="selectedType === 'int'" class="row">
      <Textfield v-model="min" :config="minField" class="col s5" @error="handleError(minField, $event)"/>
      <Textfield v-model="max" :config="maxField" class="col s6 offset-s1"
                 @error="handleError(maxField, $event)"/>
    </div>
    <div v-if="(selectedType === 'list' || selectedType === 'multiselect' || selectedType === 'editable_list')"
         class="row">
      <Textfield v-if="allowedValuesFromScript" v-model="allowedValuesScript"
                 :config="allowedValuesScriptField"
                 class="col s9" @error="handleError(allowedValuesScriptField, $event)"/>
      <ChipsList v-else v-model="allowedValues" class="col s9" title="Allowed values"
                 @error="handleError('Allowed values', $event)"/>
      <Checkbox v-model="allowedValuesFromScript" :config="allowedValuesFromScriptField"
                class="col s3"
                @error="handleError(allowedValuesFromScriptField, $event)"/>
    </div>
    <div v-if="(selectedType === 'multiselect')" class="row">
      <Checkbox v-model="multipleArguments" :config="multipleArgumentsField"
                class="col s4"
                @error="handleError(multipleArgumentsField, $event)"/>
      <Checkbox v-if="multipleArguments" v-model="sameArgParam"
                :config="sameArgParamField" class="col s3"
                @error="handleError(sameArgParamField, $event)"/>
      <Textfield v-if="!multipleArguments" v-model="separator"
                 :config="separatorField" class="col s3"
                 @error="handleError(separatorField, $event)"/>
    </div>
    <div v-if="(selectedType === 'server_file')" class="row">
      <Textfield v-model="fileDir" :config="fileDirField" class="col s5"
                 @error="handleError(fileDirField, $event)"/>
      <Checkbox v-model="recursive" :config="recursiveField" class="col s2 offset-s1"
                @error="handleError(recursiveField, $event)"/>
      <Combobox v-model="fileType" :config="fileTypeField" class="col s3 offset-s1"
                @error="handleError(fileTypeField, $event)"/>
      <ChipsList v-model="fileExtensions" class="col s12"
                 title="Allowed file extensions"
                 @error="handleError('Allowed file extensions', $event)"/>
        </div>
        <div class="row" v-if="selectedType === 'text' || selectedType === undefined">
            <Textfield :config="maxLengthField" @error="handleError(maxLengthField, $event)" class="col s4" v-model="max_length"/>
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
  constantField,
  defaultValueField,
  descriptionField,
  envVarField,
  fileDirField,
  fileTypeField,
  maxField,
  maxLengthField,
  minField,
  multipleArgumentsField,
  nameField,
  noValueField,
  recursiveField,
  repeatParamField,
  requiredField,
  sameArgParamField,
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
      repeatParam: 'repeat_param',
      envVar: 'env_var',
      type: 'type',
      noValue: 'no_value',
      required: 'required',
      constant: 'constant',
      secure: 'secure',
      min: 'min',
      max: 'max',
      max_length: 'max_length',
      multipleArguments: 'multiple_arguments',
      sameArgParam: 'same_arg_param',
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
      repeatParam: null,
      envVar: null,
      type: null,
      noValue: null,
      required: null,
      description: null,
      min: null,
      max: null,
      max_length: null,
      allowedValues: null,
      allowedValuesScript: null,
      allowedValuesFromScript: null,
      defaultValue: null,
      constant: null,
      secure: null,
      multipleArguments: null,
      sameArgParam: null,
      separator: null,
      fileDir: null,
      recursive: null,
      fileType: null,
      fileExtensions: null,
      nameField,
      argField: Object.assign({}, argField),
      repeatParamField,
      envVarField,
      typeField,
      noValueField,
      requiredField,
      secureField,
      descriptionField,
      minField,
      maxField: Object.assign({}, maxField),
      maxLengthField,
      allowedValuesScriptField,
      allowedValuesFromScriptField,
      defaultValueField: Object.assign({}, defaultValueField),
      constantField,
      multipleArgumentsField,
      sameArgParamField,
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
          this.repeatParam = !!get(config, 'repeat_param', true);
          this.envVar = config['env_var'];
          this.type = config['type'];
          this.noValue = get(config, 'no_value', false);
          this.required = get(config, 'required', false);
          this.min = config['min'];
          this.max = config['max'];
          this.max_length = config['max_length'];
          this.constant = !!get(config, 'constant', false);
          this.secure = !!get(config, 'secure', false);
          this.multipleArguments = !!get(config, 'multiple_arguments', false);
          this.sameArgParam = !!get(config, 'same_arg_param', false);
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

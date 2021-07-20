<template>
  <div :data-error="error" :title="config.description" class="input-field file-upload-field">
    <a ref="uploadButton" class="btn-icon-flat btn-small waves-effect waves-circle">
      <i class="material-icons">file_upload</i>
    </a>
    <input :id="config.name"
           ref="fileField"
           :required="config.required"
           class="validate"
           type="file"
           @blur="focused = false"
           @change="updateValue"
           @focus="focused = true"/>
    <label :for="config.name" class="file-upload-field-label" v-bind:class="{ active: (value || focused) }">
      {{ config.name }}</label>
    <label :for="config.name" class="file-upload-field-value">{{ valueText }}</label>
    <label></label>
  </div>
</template>

<script>
import {getFileInputValue, isNull} from '@/common/utils/common';

export default {
  props: {
    'value': [File],
    'config': Object
  },

  data: function () {
    return {
      error: '',
      focused: false
    }
  },

  computed: {
    valueText() {
      if (isNull(this.value)) {
        return '';
      }

      return this.value.name;
    },
  },

  mounted: function () {
    this.updateValue();

    var uploadButton = this.$refs.uploadButton;
    var fileField = this.$refs.fileField;
    uploadButton.onclick = function () {
      fileField.click();
    };
  },

  methods: {
    updateValue() {
      const fileField = this.$refs.fileField;
      let value = getFileInputValue(fileField)

      this.error = this.getValidationError(value);
      fileField.setCustomValidity(this.error);

      this.$emit('error', this.error);
      this.$emit('input', value);
    },

    getValidationError(value) {
      var empty = isNull(value);

      if (this.config.required && empty) {
        return 'required';
      }

      return '';
    }
  }
}
</script>

<style scoped>
input[type=file] {
  position: absolute;
  left: -9999px;
  opacity: 0;
}

.btn-icon-flat {
  position: absolute;
  top: 0.5em;
  right: 0;
  z-index: 1;
}

.btn-icon-flat > i {
  clip-path: inset(0 0 14px 0);
}

label {
  cursor: pointer;
}

.file-upload-field-value {
  position: static;
  display: inline-block;
  width: calc(100% - 24px);
  padding-right: 24px;
  box-sizing: content-box;

  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  vertical-align: bottom;

  /* same as text field */
  border-bottom: 1px solid var(--font-color-medium);;
  height: 3rem;
  line-height: 3rem;
  font-size: 16px;
  top: auto;
  left: auto;
  color: inherit;
  transform: none;
}

input[type="file"]:focus + * + .file-upload-field-value {
  border-bottom: 1px solid var(--primary-color);
  box-shadow: 0 1px 0 0 var(--primary-color);
}

input[type="file"]:focus + .file-upload-field-label {
  color: var(--primary-color);
}

input[type="file"]:invalid + * + .file-upload-field-value {
  border-bottom: 1px solid #e51c23;
  box-shadow: 0 1px 0 0 #e51c23;
}
</style>
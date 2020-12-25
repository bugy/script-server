<template>
    <div class="input-field file-upload-field" :title="config.description" :data-error="error">
      <a ref="uploadButton" class="btn-icon-flat btn-small waves-effect waves-circle">
        <i class="material-icons">file_upload</i>
      </a>
      <input :id="config.name"
             type="file"
             :required="config.required"
             class="validate"
             @change="updateValue"
             @blur="focused = false"
             @focus="focused = true"
             ref="fileField"/>
      <label class="file-upload-field-label" :for="config.name" v-bind:class="{ active: (value || focused) }">
            {{ config.name }}</label>
        <label class="file-upload-field-value" :for="config.name">{{ valueText }}</label>
        <label></label>
    </div>
</template>

<script>
import {isNull} from '@/common/utils/common';

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
                var fileField = this.$refs.fileField;

                var files = fileField.files;
                var value;
                if (files && (files.length > 0)) {
                    value = files[0];
                } else {
                    value = null;
                }

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
  top: -6px;
  right: -6px;
  z-index: 1;
}

.btn-icon-flat > i {
  clip-path: inset(0 0 14px 0);
}

label {
  cursor: pointer;
}

.file-upload-field-value {
  position: relative;
  display: block;
  width: 100%;
  padding-right: 24px;

  overflow: hidden;
  text-overflow: ellipsis;

  /* same as text field */
  border-bottom: 1px solid var(--font-color-medium);;
  height: 1.5rem;
  color: inherit;
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
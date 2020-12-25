<template>
  <div :data-error="error" :title="config.description" class="input-field server-file-field">
    <a ref="openFileButton" class="btn-icon-flat btn-small waves-effect waves-circle" @click="openDialog">
      <i class="material-icons">folder_open</i>
    </a>
    <input :id="config.name"
           ref="inputField"
           :required="config.required"
           :value="valueText"
           class="validate"
           readonly
           @blur="focused = false"
           @click="openDialog"
           @focus="focused = true"
           @keypress.enter.prevent="openDialog"
           @keypress.space.prevent="openDialog"/>
    <label :for="config.name"
           v-bind:class="{ active: ((value && value.length > 0) || focused) }">{{ config.name }}</label>
    <div ref="modal" class="modal">
      <FileDialog ref="fileDialog" :fileType="this.config.fileType"
                  :loadFiles="this.config.loadFiles"
                  :onClose="dialogClosed"
                  :onFileSelect="selectFile"
                  :opened="dialogOpened"
                  class="file-dialog"/>
    </div>
  </div>
</template>

<script>
import '@/common/materializecss/imports/modal';
import {addClass, arraysEqual, getTextWidth, isEmptyArray, isNull, removeClass} from '@/common/utils/common';
import FileDialog from './file_dialog'

export default {
  name: 'server_file_field',

  components: {
    FileDialog
  },

  props: {
    'value': [Array],
    'config': Object
  },

  data: function () {
    return {
      error: '',
      focused: false,
      dialogOpened: false,
      isMounted: false
    }
  },

  computed: {
    valueText() {
      if (isEmptyArray(this.value)) {
        return '';
      }

      const valueText = this.value.join('/');
      if (!this.isMounted || !this.$refs.inputField) {
        return valueText;
      }

      const textWidth = getTextWidth(valueText, this.$refs.inputField);
      const availableWidth = this.$refs.inputField.offsetWidth - this.$refs.openFileButton.offsetWidth;

      if (textWidth <= availableWidth) {
        return valueText;
      }

      const characterWidth = textWidth / valueText.length;
      let cutLength = (availableWidth) / characterWidth - 2; // 2 is width for ellipsis

      let cutValue;
      do {
        cutValue = '...' + valueText.substring(valueText.length - cutLength);
        const valueWidth = getTextWidth(cutValue, this.$refs.inputField);

        if (valueWidth <= availableWidth) {
          break;
        }
        cutLength--;

      } while (cutLength > 0);


      return cutValue;
    }
  },

  mounted: function () {
    M.Modal.init(this.$refs.modal, {onCloseEnd: this.dialogClosed});

    this.isMounted = true;
  },

  beforeDestroy: function () {
    const modal = M.Modal.getInstance(this.$refs.modal);
    modal.destroy();
  },

  methods: {
    selectFile(path) {
      this.error = this.getValidationError(path);

      var inputField = this.$refs.inputField;
      if (!isNull(inputField)) {
        // setCustomValidity doesn't work since input is readonly
        if (this.error) {
          addClass(inputField, 'invalid');
        } else {
          removeClass(inputField, 'invalid');
        }
      }

      this.closeDialog();

      this.$emit('error', this.error);

      if (!arraysEqual(this.value, path)) {
        this.$emit('input', path);
      }
    },

    getValidationError(path) {
      var empty = isEmptyArray(path);

      if (this.config.required && empty) {
        return 'required';
      }

      return '';
    },

    dialogClosed() {
      this.closeDialog();
    },

    closeDialog() {
      const modal = M.Modal.getInstance(this.$refs.modal);
      modal.close();

      this.$refs.inputField.focus();
      this.dialogOpened = false;
    },

    openDialog(event) {
      const modal = M.Modal.getInstance(this.$refs.modal);
      modal.open();

      this.$refs.fileDialog.setChosenFile(this.value);
      this.dialogOpened = true;
      this.$refs.fileDialog.focus();
    }
  }
}
</script>

<style scoped>
.btn-icon-flat {
  position: absolute;
  top: -8px;
  right: -4px;
  z-index: 1;
}

.btn-icon-flat > i {
  font-size: 1.4rem;
}

.server-file-field .modal {
  width: fit-content;
  width: -moz-fit-content;
  height: 70%;
  min-height: 300px;
}

.server-file-field .file-dialog {
  height: 100%;
}

.server-file-field input[readonly] {
  user-select: none;
  color: var(--font-color-main);
  border-bottom: 1px solid var(--font-color-medium);
}

.server-file-field input[readonly] + label {
  color: var(--font-color-medium);
}

.server-file-field input:focus {
  border-bottom: 1px solid var(--primary-color);
  box-shadow: 0 1px 0 0 var(--primary-color);
}

.server-file-field input:focus + label {
  color: var(--primary-color);
}

</style>
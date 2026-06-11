<template>
  <div :data-error="error" :title="config.description" class="server-file-field">
    <v-text-field
        ref="field"
        :error-messages="errorMessages"
        :label="config.name"
        :model-value="valueText"
        :required="config.required"
        append-inner-icon="folder_open"
        readonly
        @click:append-inner="openDialog"
        @mousedown="openDialog"
        @keydown.enter.prevent="openDialog"
        @keydown.space.prevent="openDialog"/>

    <v-dialog v-model="dialogOpened" class="server-file-dialog" width="auto">
      <FileDialog ref="fileDialog" :fileType="config.fileType"
                  :loadFiles="config.loadFiles"
                  :onClose="closeDialog"
                  :onFileSelect="selectFile"
                  :opened="dialogOpened"
                  class="file-dialog"/>
    </v-dialog>
  </div>
</template>

<script>
// Vuetify migration: v-text-field (readonly, folder icon inside the field)
// + v-dialog replace the materialize input + M.Modal. FileDialog itself is
// untouched — it never depended on materialize JS. Validation (required)
// and the open-on-click/Enter/Space behaviours are unchanged.
import {arraysEqual, getTextWidth, isEmptyArray, isEmptyString, isNull} from '@/common/utils/common';
import FileDialog from './file_dialog'

export default {
  name: 'server_file_field',

  emits: ['update:modelValue', 'error'],
  components: {
    FileDialog
  },

  props: {
    'modelValue': [Array],
    'config': Object
  },

  data: function () {
    return {
      error: '',
      dialogOpened: false,
      isMounted: false
    }
  },

  computed: {
    errorMessages() {
      return isEmptyString(this.error) ? [] : [this.error];
    },

    valueText() {
      if (isEmptyArray(this.modelValue)) {
        return '';
      }

      const valueText = this.modelValue.join('/');
      const inputField = this.isMounted ? this.nativeInput() : null;
      if (isNull(inputField)) {
        return valueText;
      }

      const textWidth = getTextWidth(valueText, inputField);
      const availableWidth = inputField.offsetWidth;

      if (!availableWidth || (textWidth <= availableWidth)) {
        return valueText;
      }

      const characterWidth = textWidth / valueText.length;
      let cutLength = (availableWidth) / characterWidth - 2; // 2 is width for ellipsis

      let cutValue;
      do {
        cutValue = '...' + valueText.substring(valueText.length - cutLength);
        const valueWidth = getTextWidth(cutValue, inputField);

        if (valueWidth <= availableWidth) {
          break;
        }
        cutLength--;

      } while (cutLength > 0);


      return cutValue;
    }
  },

  mounted: function () {
    this.isMounted = true;

    this.validate(this.modelValue)
  },

  methods: {
    nativeInput() {
      return this.$refs.field?.$el?.querySelector('input') ?? null;
    },

    selectFile(path) {
      this.closeDialog();

      this.validate(path)

      if (!arraysEqual(this.modelValue, path)) {
        this.$emit('update:modelValue', path);
      }
    },

    getValidationError(path) {
      var empty = isEmptyArray(path);

      if (this.config.required && empty) {
        return 'required';
      }

      return '';
    },

    closeDialog() {
      this.dialogOpened = false;

      this.$refs.field?.focus();
    },

    openDialog() {
      if (this.dialogOpened) {
        return;
      }

      this.dialogOpened = true;

      this.$nextTick(() => {
        this.$refs.fileDialog.setChosenFile(this.modelValue);
        this.$refs.fileDialog.focus();
      });
    },

    validate(path) {
      this.error = this.getValidationError(path);

      this.$emit('error', this.error);
    }
  }
}

</script>

<style scoped>
.server-file-field :deep(.v-field__input) {
  cursor: pointer;
}

.server-file-dialog :deep(.file-dialog) {
  background-color: var(--background-color, #fff);
}
</style>

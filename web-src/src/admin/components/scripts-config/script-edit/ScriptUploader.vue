<template>
  <div class="script-uploader">
    <Textfield :config="uploadToFieldConfig" :disabled="!pathEditable" :value="path"/>
    <File_upload v-if="!codeLoadingError"
                 :config="localScriptFieldConfig"
                 :value="value"
                 @error="$emit('error', $event)"
                 @input="$emit('input', $event)"/>
    <div v-if="codeLoadingError" class="info-text error">{{ codeLoadingError }}</div>
  </div>
</template>

<script>
import Textfield from '@/common/components/textfield'
import File_upload from '@/common/components/file_upload'

export default {
  name: 'ScriptUploader',
  components: {File_upload, Textfield},
  props: {
    path: {
      type: String
    },
    pathEditable: {
      type: Boolean
    },
    value: null,
    codeLoadingError: String
  },
  data() {
    return {
      uploadToFieldConfig: {
        name: 'Upload to',
        required: true
      },
      localScriptFieldConfig: {
        name: 'Local script',
        required: true
      }
    }
  }
}
</script>

<style scoped>
.file-upload-field {
  margin-top: 24px;
}

.info-text {
  font-size: 1.1rem;
  margin-top: 12px;
}

.error {
  color: var(--error-color);
}
</style>
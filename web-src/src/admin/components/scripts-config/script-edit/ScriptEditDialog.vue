<template>
  <div ref="modal" :class="{large:inEditorMode}" class="modal script-edit-dialog">
    <div class="card">
      <div class="card-content">
        <RadioGroup v-model="editMode"
                    :horizontal="true"
                    :options="modeOptions"
                    group-name="script-edit-mode"/>

        <Textfield v-show="inPathMode" ref="plainPathField"
                   v-model="plainPath"
                   :config="pathFieldConfig"
                   @error="$set(modeErrors, 'new_path', $event)"/>
        <CodeEditor v-show="inEditorMode" ref="codeEditor"
                    :code-loaded="codeLoaded"
                    :loading-error="codeLoadingError || codeLoadingEditorError"
                    :new-file="newConfig"
                    :original-code="originalCode"
                    :path="editorScriptPath"
                    :path-editable="false"
                    @input="code = $event"
                    @languageChange="editorLanguageConfig = $event"/>
        <ScriptUploader v-show="inUploadMode"
                        ref="scriptUploader"
                        v-model="uploadedScript"
                        :code-loading-error="codeLoadingError"
                        :path="targetUploadPath"
                        @error="$set(modeErrors, 'upload_script', $event)"/>
      </div>
      <div :class="{borderless: inEditorMode}" class="card-action">
        <span v-if="hasIgnoredChanges" class="ignored-changes-warning valign-wrapper">
          <i class="material-icons">error_outline</i>
          Changes in non-active tabs will be ignored
        </span>
        <span v-else/>

        <span>
        <a class="btn-flat" @click="closeDialog">
          Cancel
        </a>
        <a :class="{disabled: saveDisabled}" :disabled="saveDisabled" class="btn-flat" @click="onSave">
          Save
        </a>
          </span>
      </div>
    </div>

  </div>
</template>

<script>
import '@/common/materializecss/imports/modal'
import RadioGroup from '@/common/components/RadioGroup'
import CodeEditor from '@/admin/components/scripts-config/script-edit/CodeEditor'
import Textfield from '@/common/components/textfield'
import ScriptUploader from '@/admin/components/scripts-config/script-edit/ScriptUploader'
import cloneDeep from 'lodash/cloneDeep'
import {isBlankString, isEmptyString, isNull} from '@/common/utils/common'
import {axiosInstance} from '@/common/utils/axios_utils'
import get from 'lodash/get';

const EDITOR_MODE_TEXT = 'Edit script code'
export const EDITOR_MODE = 'new_code'
const PATH_MODE_TEXT = 'Path on server'
export const PATH_MODE = 'new_path'
const UPLOAD_MODE_TEXT = 'Upload script'
export const UPLOAD_MODE = 'upload_script'

const defaultModeOptions = [
  {
    value: PATH_MODE,
    text: PATH_MODE_TEXT
  },
  {
    value: EDITOR_MODE,
    text: EDITOR_MODE_TEXT
  },
  {
    value: UPLOAD_MODE,
    text: UPLOAD_MODE_TEXT
  },
]

const defaultScriptsFolder = './conf/scripts/'

export default {
  name: 'ScriptEditDialog',
  props: {
    newConfig: Boolean,
    originalPath: String,
    configName: String,
    inputPlainPath: String
  },
  created() {
    if (!this.newConfig) {
      axiosInstance.get('/admin/scripts/' + encodeURIComponent(this.configName) + '/code')
          .then(({data}) => {
            this.code = data.code
            this.originalCode = data.code
            this.codeLoaded = true
            this.codeLoadingEditorError = data['code_edit_error']

            if (!isBlankString(this.codeLoadingEditorError)) {
              this.$set(this.modeErrors, EDITOR_MODE, this.codeLoadingEditorError)
            }
          })
          .catch(error => {
            const status = get(error, 'response.status')

            let errorText = 'Could not load code, please check logs'
            if ((status === 422) || (status === 403)) {
              errorText = get(error, 'response.data')
            }

            this.$set(this.modeErrors, EDITOR_MODE, errorText)
            this.codeLoadingError = errorText
          });
    }
  },
  data() {
    return {
      open: false,
      editMode: 'new_path',
      modeOptions: cloneDeep(defaultModeOptions),
      originalCode: '',
      codeLoaded: this.newConfig,
      codeLoadingError: null,
      codeLoadingEditorError: null,
      code: '',
      uploadedScript: null,
      plainPath: '',
      editorScriptPath: (this.newConfig || !this.originalPath) ? defaultScriptsFolder : this.originalPath,
      editorLanguageConfig: null,
      targetUploadPath: (this.newConfig || !this.originalPath) ? defaultScriptsFolder : this.originalPath,
      pathFieldConfig: {
        name: 'Path or command',
        required: true
      },
      hasIgnoredChanges: false,
      modeErrors: {}
    }
  },
  components: {ScriptUploader, Textfield, RadioGroup, CodeEditor},
  mounted() {
    M.Modal.init(this.$refs.modal, {
      onCloseStart: () => this.open = false
    })

    this.openDialog()

    this.$refs.modal.addEventListener('transitionend', () => this.$refs.codeEditor.resize())
  },
  beforeDestroy() {
    const modal = M.Modal.getInstance(this.$refs.modal)
    modal.destroy()
  },
  computed: {
    inEditorMode() {
      return this.editMode === EDITOR_MODE;
    },
    inPathMode() {
      return this.editMode === PATH_MODE;
    },
    inUploadMode() {
      return this.editMode === UPLOAD_MODE;
    },
    saveDisabled() {
      const error = this.modeErrors[this.editMode]
      return !isEmptyString(error)
    }
  },
  methods: {
    openDialog() {
      const modal = M.Modal.getInstance(this.$refs.modal)
      modal.open()

      this.$nextTick(() => {
        this.open = true
        this.focusOnModeSwitch()
      })
      M.updateTextFields()
    },
    closeDialog() {
      const modal = M.Modal.getInstance(this.$refs.modal)
      modal.close()
    },
    onSave() {
      this.emitNewValue()
      this.closeDialog()
    },
    emitNewValue() {
      let newValue
      if (this.inEditorMode) {
        newValue = {
          path: this.editorScriptPath,
          code: this.code,
          mode: this.editMode
        }
      } else if (this.inUploadMode) {
        newValue = {
          path: this.targetUploadPath,
          uploadFile: this.uploadedScript,
          mode: this.editMode
        }
      } else {
        newValue = {
          path: this.plainPath,
          mode: this.editMode
        }
      }

      this.$emit('change', newValue)
    },
    updateEditorScriptPath() {
      if (!this.newConfig) {
        return
      }

      if (isNull(this.editorLanguageConfig)) {
        return
      }

      const filename = isBlankString(this.configName) ? '{name}' : this.configName.trim()
      this.editorScriptPath = defaultScriptsFolder + filename + '.' + this.editorLanguageConfig.extensions[0]
    },
    focusOnModeSwitch() {
      if (this.inEditorMode) {
        this.$refs.codeEditor.focus()
      } else if (this.inPathMode) {
        this.$refs.plainPathField.focus()
      }
    }
  },
  watch: {
    inputPlainPath: {
      immediate: true,
      handler() {
        this.plainPath = this.inputPlainPath
      }
    },
    originalCode: {
      immediate: true,
      handler(newCode) {
        this.code = newCode
      }
    },
    uploadedScript() {
      if (!this.newConfig) {
        return
      }

      if (this.uploadedScript) {
        this.targetUploadPath = defaultScriptsFolder + this.uploadedScript.name
      } else {
        this.targetUploadPath = defaultScriptsFolder
      }
    },
    editMode() {
      let changedModes = []

      if ((this.originalCode !== this.code) && (!this.$refs.codeEditor.isDefaultCode())) {
        changedModes.push(EDITOR_MODE)
      }

      if (!isNull(this.uploadedScript)) {
        changedModes.push(UPLOAD_MODE)
      }

      if (isEmptyString(this.originalPath)) {
        if (!isEmptyString(this.plainPath)) {
          changedModes.push(PATH_MODE)
        }
      } else if (isEmptyString(this.plainPath) || (this.originalPath !== this.plainPath)) {
        changedModes.push(PATH_MODE)
      }

      this.hasIgnoredChanges = false

      for (const option of this.modeOptions) {
        if (changedModes.includes(option.value) && option.value !== this.editMode) {
          option.icon = 'error_outline'
          option.iconTitle = 'Changes will be ignored'
          this.hasIgnoredChanges = true
        } else {
          option.icon = null
          option.iconTitle = null
        }
      }

      this.$nextTick(() => this.focusOnModeSwitch())
    },
    editorLanguageConfig: {
      immediate: true,
      handler() {
        this.updateEditorScriptPath()
      }
    },
    configName: {
      immediate: true,
      handler() {
        this.updateEditorScriptPath()
      }
    },
    editorScriptPath() {
      if (!this.open && this.inEditorMode) {
        this.emitNewValue()
      }
    },
    codeLoaded() {
      if (this.inEditorMode && this.codeLoaded) {
        this.$refs.codeEditor.focus()
      }
    }
  },
}
</script>

<style scoped>
.modal {
  max-height: 80%;
  height: 300px;

  width: 70%;
  min-width: 780px;

  transition: height 0.3s;
}

.modal.large {
  height: 80%;
}

@media screen and (max-width: 800px) {
  .modal {
    width: calc(100vw - 16px);
    min-width: 0;
  }
}

.card .card-content {
  padding-bottom: 0;
  display: flex;
  flex-direction: column;
}

.card .card-action {
  padding-top: 8px;
  padding-bottom: 8px;
  padding-right: 0;
  justify-content: space-between;
}

.card .card-action.borderless {
  border-top: none;
}

.radio-group {
  flex: 0 0 auto;
  margin-bottom: 16px;
}

.code-editor {
  flex: 1 1 auto;
}

.ignored-changes-warning {
  line-height: 36px;
  color: var(--font-color-medium)
}

.ignored-changes-warning i {
  margin-right: 8px;
}

</style>
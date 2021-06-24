<template>
  <div class="script-path-field">
    <div @click.capture="activateTextField"
         @keydown.capture="activateTextField">
      <TextField :config="scriptPathField"
                 :value="inPathMode ? plainPath : scriptValue.path"
                 class="path-textfield"
                 @input="onPathInput"/>

      <a v-if="canEditCode"
         v-trim-text
         class="btn-icon-flat waves-effect waves-circle btn-large open-dialog-button"
         title="Script editor"
         @click="openScriptDialog()">
        <i class="material-icons">{{ actionIcon }}</i>
      </a>
    </div>

    <ScriptEditDialog v-if="dialogInitialized" ref="dialog"
                      :config-name="configName"
                      :input-plain-path="plainPath"
                      :new-config="newConfig"
                      :original-path="originalPath"
                      @change="onScriptChange"/>
  </div>
</template>

<script>
import {scriptPathField} from '@/admin/components/scripts-config/script-fields'
import Combobox from '@/common/components/combobox'
import TextField from '@/common/components/textfield'
import CodeEditorDialog, {
  EDITOR_MODE,
  PATH_MODE,
  UPLOAD_MODE
} from '@/admin/components/scripts-config/script-edit/ScriptEditDialog'
import CodeEditor from '@/admin/components/scripts-config/script-edit/CodeEditor'
import {isNull} from '@/common/utils/common'
import {mapState} from 'vuex'

const ScriptEditDialog = () => import('@/admin/components/scripts-config/script-edit/ScriptEditDialog')

export default {
  name: 'ScriptPathField',
  components: {ScriptEditDialog, Combobox, TextField, CodeEditorDialog, CodeEditor},
  props: {
    originalPath: String,
    newConfig: Boolean,
    configName: String,
    testMode: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      dialogInitialized: false,
      scriptPathField: Object.assign({}, scriptPathField),
      scriptValue: {path: this.originalPath || '', mode: PATH_MODE},
      plainPath: this.originalPath,
      actionIcon: 'more_vert'
    }
  },
  computed: {
    inPathMode() {
      return isNull(this.scriptValue.mode) || (this.scriptValue.mode === PATH_MODE);
    },
    ...mapState('auth', {
      canEditCode: 'canEditCode'
    }),
  },
  methods: {
    openScriptDialog() {
      if (this.dialogInitialized) {
        this.$refs.dialog.openDialog()
        return
      }

      this.dialogInitialized = true
    },
    onScriptChange(newScript) {
      if (newScript.mode === EDITOR_MODE) {
        this.actionIcon = 'subject'
        this.scriptPathField.name = 'Code changes'
      } else if (newScript.mode === UPLOAD_MODE) {
        this.actionIcon = 'file_upload'
        this.scriptPathField.name = 'Upload to'
      } else {
        this.actionIcon = 'more_vert'
        this.scriptPathField.name = 'Script path'
        this.plainPath = newScript.path
      }

      this.$emit('change', newScript)
      this.scriptValue = newScript
    },
    activateTextField(event) {
      if (event instanceof KeyboardEvent) {
        if (event.altKey || event.ctrlKey || event.metaKey || (event.code === 'Tab')) {
          return;
        }
      }

      if (!this.inPathMode) {
        event.preventDefault()
        this.openScriptDialog()
      }
    },
    onPathInput(newPath) {
      if (this.inPathMode) {
        this.plainPath = newPath
        this.onScriptChange({...this.scriptValue, path: newPath})
      }
    }
  }
}
</script>

<style scoped>
.script-path-field {
  position: relative;
}

.open-dialog-button {
  position: absolute;
  right: 0;
  top: 12px;
}

>>> .input-field:after {
  left: 0;
}

>>> .path-textfield input {
  padding-right: 1em;
  box-sizing: border-box;
  text-overflow: ellipsis;
}
</style>
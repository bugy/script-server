<template>
  <div :class="{'light-theme': lightTheme}" class="code-editor">
    <div class="row">
      <Textfield :config="pathField" :disabled="!pathEditable"
                 :value="path"
                 class="inline col s8"
                 @input="$emit('pathChanged', $event)"/>
      <Combobox v-model="language" :config="languagesConfig" :dropdownContainer="dropdownContainer"
                class="inline col l2 offset-l2 m3 offset-m1 s3 offset-s1"/>
    </div>

    <div v-show="codeLoaded && !loadingError" ref="editor" class="editor"/>

    <div v-if="loadingError" v-trim-text class="info-text error">{{ loadingError }}</div>
    <div v-else-if="!codeLoaded" class="info-text">Loading code...</div>
  </div>

</template>

<script>
import ace from 'ace-builds/src-noconflict/ace'
import 'ace-builds/src-noconflict/theme-monokai'
import Checkbox from '@/common/components/checkbox'
import tinycolor from 'tinycolor2'
import '@/common/materializecss/imports/cards';
import Combobox from '@/common/components/combobox'
import Textfield from '@/common/components/textfield'
import {forEachKeyValue, isEmptyString, isNull} from '@/common/utils/common'

ace.config.setModuleUrl('ace/theme/monokai', require('file-loader!ace-builds/src-noconflict/theme-monokai'))
ace.config.setModuleUrl('ace/mode/javascript', require('file-loader!ace-builds/src-noconflict/mode-javascript.js'))
ace.config.setModuleUrl('ace/mode/python', require('file-loader!ace-builds/src-noconflict/mode-python.js'))
ace.config.setModuleUrl('ace/mode/sh', require('file-loader!ace-builds/src-noconflict/mode-sh.js'))
ace.config.setModuleUrl('ace/mode/powershell', require('file-loader!ace-builds/src-noconflict/mode-powershell.js'))
ace.config.setModuleUrl('ace/mode/raku', require('file-loader!ace-builds/src-noconflict/mode-raku.js'))
ace.config.setModuleUrl('ace/mode/r', require('file-loader!ace-builds/src-noconflict/mode-r.js'))


const allowedLanguages = {
  'python': {aceName: 'python', extensions: ['py'], shebang: '#!/usr/bin/env python\n'},
  'bash': {aceName: 'sh', extensions: ['sh'], shebang: '#!/bin/bash\n'},
  'powershell': {aceName: 'powershell', extensions: ['ps1', 'psc1'], shebang: '#!/usr/bin/env pwsh\n'},
  'perl': {aceName: 'raku', extensions: ['pl'], shebang: '#!/usr/bin/env perl\n'},
  'R': {aceName: 'r', extensions: ['r'], shebang: '#!/usr/bin/env Rscript\n'}
}

export default {
  name: 'CodeEditor',
  components: {Textfield, Combobox, Checkbox},
  props: {
    path: String,
    originalCode: String,
    pathEditable: Boolean,
    codeLoaded: Boolean,
    loadingError: String,
    newFile: Boolean
  },
  data() {
    return {
      editor: null,
      python: false,
      language: 'python',
      languagesConfig: {
        'name': 'Syntax',
        'values': Object.keys(allowedLanguages)
      },
      dropdownContainer: document.body,
      pathField: {
        name: 'Script path',
        required: true
      },
      lightTheme: true
    }
  },
  mounted() {
    const editor = ace.edit(this.$refs.editor)

    editor.getSession().setOption('useWorker', false);
    editor.setOptions({
      autoScrollEditorIntoView: true,
      copyWithEmptySelection: true,
      fontSize: 13
    })
    editor.getSession().on('change', () => {
      this.$emit('input', editor.getSession().getValue())
    })

    const backgroundColor = getComputedStyle(this.$el).getPropertyValue('--background-color')
    if (tinycolor(backgroundColor).isDark()) {
      editor.setTheme('ace/theme/monokai')
      this.lightTheme = false
    }

    if (this.codeLoaded) {
      editor.setValue(this.originalCode, -1)

      if (this.newFile && isEmptyString(this.originalCode) && this.language) {
        editor.setValue(allowedLanguages[this.language].shebang, 1)
      }
    }

    this.editor = editor

    this.selectSyntax()
  },
  beforeDestroy() {
    this.editor.container.remove()
    this.editor.destroy()
  },
  watch: {
    originalCode() {
      if (isNull(this.editor) || isNull(this.originalCode)) {
        return
      }

      this.editor.setValue(this.originalCode, -1)
    },
    path: {
      immediate: true,
      handler(newName) {
        const extension = newName.split('.').pop()
        if (isEmptyString(extension)) {
          return
        }

        forEachKeyValue(allowedLanguages, (key, value) => {
          if (value.extensions.includes(extension.toLowerCase())) {
            this.language = key
          }
        })
      }
    },
    language: {
      immediate: true,
      handler(newLang, oldLang) {
        const languageConfig = allowedLanguages[this.language]
        this.$emit('languageChange', languageConfig)

        if (this.$refs.editor) {
          this.selectSyntax()

          if (this.newFile) {
            if (isEmptyString(oldLang) || this.editor.getValue().trim() === allowedLanguages[oldLang].shebang.trim()) {
              this.editor.setValue(languageConfig.shebang, 1)
              this.focus()
            }
          }
        }
      }
    }
  },
  methods: {
    selectSyntax() {
      const editorLanguage = allowedLanguages[this.language].aceName
      this.editor.getSession().setMode('ace/mode/' + editorLanguage)
    },
    resize() {
      this.editor.resize()
    },
    focus() {
      this.editor.focus()
    },
    isDefaultCode() {
      if (!this.newFile) {
        return false
      }

      const code = this.editor.getValue().trim()
      if (isEmptyString(code)) {
        return true
      }

      if (!this.language) {
        return false
      }

      return code === allowedLanguages[this.language].shebang.trim()
    }
  },
  computed: {},
}
</script>

<style scoped>
.code-editor {
  margin-top: 8px;
  width: 100%;
  height: 100%;
}

.editor {
  width: 100%;
  position: relative;
  height: calc(100% - 54px);
}

.row {
  margin: 0;
}

.col {
  padding-left: 0;
  padding-right: 0;
}

>>> .input-field.col label {
  left: 0
}

>>> .input-field > label:not(.label-icon).active {
  transform: translateY(-12px) scale(0.8);
}

>>> .input-field input {
  height: 2.6rem;
}

.input-field.inline {
  margin-bottom: 0;
  margin-top: 0;
}

.info-text {
  font-size: 1.1rem;
  margin-top: 12px;
}

.error {
  color: var(--error-color);
}

.light-theme .editor {
  border: 1px solid var(--outline-color);
}
</style>
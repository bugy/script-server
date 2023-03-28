<template>
  <div ref="parametersPanel" :style="{ 'grid-template-columns': 'repeat(' + gridColumns + ', minmax(0, 1fr))'}"
       class="script-parameters-panel">
    <template v-for="parameter in parameters">
      <ParameterSeparator
          v-if="parameter.ui?.separatorBefore && !startsWithNewLine(parameter)"
          :separator="parameter.ui?.separatorBefore"
          :style="'grid-column-start: span ' + gridColumns"/>
      <component
          :is="getComponentType(parameter)"
          :key="parameter.name"
          :config="parameter"
          :value="getParameterValue(parameter)"
          :class="{'inline': isInline(parameter)}"
          class="parameter"
          :style="getGridCellStyle(parameter)"
          :forceValue="forcedValueParameters.includes(parameter.name)"
          @error="handleError(parameter, $event)"
          @input="setParameterValue(parameter.name, $event)"/>
    </template>
  </div>
</template>

<script>
import Checkbox from '@/common/components/checkbox'
import Combobox from '@/common/components/combobox'
import FileUpload from '@/common/components/file_upload'
import ServerFileField from '@/common/components/server_file_field'
import TextArea from '@/common/components/TextArea'
import Textfield from '@/common/components/textfield'
import {isNull} from '@/common/utils/common';
import ParameterSeparator from '@/main-app/components/scripts/ParameterSeparator.vue';
import {mapActions, mapState} from 'vuex'
import {comboboxTypes, isRecursiveFileParameter} from '../../utils/model_helper'

export default {
  name: 'script-parameters-view',
  components: {ParameterSeparator},

  data: function () {
    return {
      gridColumns: 7
    }
  },

  computed: {
    ...mapState('scriptConfig', {
      parameters: 'parameters'
    }),
    ...mapState('scriptSetup', {
      parameterValues: 'parameterValues',
      forcedValueParameters: 'forcedValueParameters'
    })
  },

  mounted() {
    window.addEventListener('resize', this.recalculateParamsLayout)

    this.$nextTick(() => {
      this.recalculateParamsLayout()
    })
  },

  beforeDestroy() {
    window.removeEventListener('resize', this.recalculateParamsLayout)
  },

  methods: {
    ...mapActions('scriptSetup', {
      setParameterValueInStore: 'setParameterValue',
      setParameterErrorInStore: 'setParameterError'
    }),
    getComponentType(parameter) {
      if (parameter.withoutValue) {
        return Checkbox;
      } else if (isRecursiveFileParameter(parameter)) {
        return ServerFileField;
      } else if (comboboxTypes.includes(parameter.type)) {
        return Combobox;
      } else if (parameter.type === 'file_upload') {
        return FileUpload;
      } else if (parameter.type === 'multiline_text') {
        return TextArea;
      } else {
        return Textfield;
      }
    },

    isInline(parameter) {
      return parameter.type !== 'multiline_text'
    },

    handleError(parameter, error) {
      this.setParameterErrorInStore({parameterName: parameter.name, errorMessage: error})
    },

    setParameterValue(parameterName, value) {
      this.setParameterValueInStore({parameterName, value});
    },

    getParameterValue(parameter) {
      const value = this.parameterValues[parameter.name];
      if (!isNull(value)) {
        return value;
      }

      if (parameter.withoutValue) {
        return false;
      }

      return value;
    },

    recalculateParamsLayout() {
      const width = this.$refs.parametersPanel.clientWidth
      const minCellWidth = 200

      this.gridColumns = Math.floor(width / minCellWidth)
    },

    getGridCellStyle(parameter) {
      if (this.isInline(parameter)) {
        const styles = []

        if (this.startsWithNewLine(parameter)) {
          styles.push('grid-column-start: 1')
        }

        let widthWeight = parameter.ui?.['widthWeight'];
        if (widthWeight) {
          styles.push('grid-column-end: span ' + Math.min(widthWeight, this.gridColumns))
        }

        return styles.join('; ')
      }

      return 'grid-column-end: span ' + this.gridColumns
    },

    startsWithNewLine(parameter) {
      const separator = parameter.ui?.separatorBefore
      if (isNull(separator)) {
        return false
      }

      if (separator.title) {
        return false
      }

      return separator.type === 'new_line'
    }
  }
}
</script>

<style scoped>
.script-parameters-panel >>> {
  margin-top: 15px;
  margin-right: 0;
  display: grid;
  gap: 24px;
  row-gap: 8px;
}

.script-parameters-panel >>> .parameter.inline {
  margin-left: 0;
}

.script-parameters-panel >>> .parameter input,
.script-parameters-panel >>> .parameter textarea,
.script-parameters-panel >>> .parameter .file-upload-field-value {
  margin: 0;

  font-size: 1rem;
  height: 1.5em;
  line-height: 1.5em;
}

.script-parameters-panel >>> .parameter textarea {
  padding-bottom: 0;
  padding-top: 0;

  min-height: 1.5em;
  box-sizing: content-box;
}

.script-parameters-panel >>> .parameter > label {
  transform: none;
  font-size: 1rem;
}

.script-parameters-panel >>> .parameter > label.active {
  transform: translateY(-70%) scale(0.8);
}

.script-parameters-panel >>> .input-field input[type=checkbox] + span {
  padding-left: 28px;
}

.script-parameters-panel >>> .input-field .select-wrapper + label {
  transform: scale(0.8);
  top: -18px;
}

.script-parameters-panel >>> .input-field:after {
  top: 1.7em;
  left: 0.1em;
}

.script-parameters-panel >>> .file-upload-field .btn-icon-flat {
  top: -7px;
  right: -4px;
}

.script-parameters-panel >>> .dropdown-content {
  max-width: 50vw;
  min-width: 100%;
  white-space: nowrap;

  margin-bottom: 0;
}

.script-parameters-panel >>> .dropdown-content > li > span {
  overflow-x: hidden;
  text-overflow: ellipsis;
}

</style>

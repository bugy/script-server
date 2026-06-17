<template>
  <div class="script-param-list">
    <v-expansion-panels
      ref="parametersPanel"
      v-model="openedPanel"
      variant="popout"
      class="param-panels"
    >
      <ParamListItem
        v-for="param in parameters"
        :key="paramKeys.get(param)"
        :param="param"
        :panel-value="paramKeys.get(param)"
        @delete="deleteParam(param)"
        @move-down="moveDown(param)"
        @move-up="moveUp(param)"
      />
    </v-expansion-panels>

    <div class="add-param-item" @click.stop="addParam">
      <v-icon>add</v-icon>Add
    </div>

    <v-snackbar v-model="snackbarVisible" :timeout="8000">
      {{ snackbarMessage }}
      <template #actions>
        <v-btn variant="text" @click="undoDelete">Undo</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script>
import {guid} from '@/common/utils/common'
import ParamListItem from './ParamListItem';

export default {
  name: 'ScriptParamList',

  components: {ParamListItem},

  props: {
    parameters: {
      type: Array,
      default: () => []
    }
  },

  data() {
    return {
      openingNewParam: false,
      paramKeys: new Map(),
      openedPanel: undefined,
      snackbarVisible: false,
      snackbarMessage: '',
      undoQueue: []
    }
  },

  beforeUnmount() {
    clearInterval(this.scrollInterval);
  },

  methods: {
    deleteParam(param) {
      const index = this.parameters.indexOf(param);
      if (index < 0) {
        return;
      }

      this.parameters.splice(index, 1);

      this.undoQueue.push({param, index});
      this.snackbarMessage = 'Deleted ' + param.name;
      this.snackbarVisible = true;
    },

    undoDelete() {
      if (!this.undoQueue.length) {
        return;
      }

      const {param, index} = this.undoQueue.shift();
      const insertPosition = Math.min(index, this.parameters.length);
      this.parameters.splice(insertPosition, 0, param);

      if (!this.undoQueue.length) {
        this.snackbarVisible = false;
      }
    },

    moveUp(param) {
      const index = this.parameters.indexOf(param);
      if (index <= 0) {
        return;
      }

      const prevParam = this.parameters[index - 1];
      this.parameters[index - 1] = param;
      this.parameters[index] = prevParam;
    },

    moveDown(param) {
      const index = this.parameters.indexOf(param);
      if ((index < 0) || (index > this.parameters.length - 2)) {
        return;
      }

      const nextParam = this.parameters[index + 1];
      this.parameters[index + 1] = param;
      this.parameters[index] = nextParam;
    },

    addParam() {
      const lastIndex = this.parameters.length;

      const newParameter = {
        name: undefined,
        param: undefined,
        repeat_param: undefined,
        description: undefined,
        default: undefined,
        constant: undefined,
        min: undefined,
        max: undefined,
        no_value: undefined,
        values: undefined,
        file_extensions: undefined,
        type: undefined,
        required: undefined,
        secure: undefined,
        multiple_arguments: undefined,
        same_arg_param: undefined,
        separator: undefined,
        file_recursive: undefined,
        file_type: undefined
      };
      this.parameters.splice(lastIndex, 0, newParameter);

      this.setParameterKey(newParameter);

      this.$nextTick(() => {
        this.openingNewParam = true;
        this.openedPanel = this.paramKeys.get(newParameter);
      });
    },

    scrollToNewParam() {
      const panelRef = this.$refs.parametersPanel;
      if (!panelRef) {
        return;
      }

      const el = panelRef.$el || panelRef;
      const parameterElements = el.querySelectorAll('.v-expansion-panel');
      const newParamElement = parameterElements[parameterElements.length - 1];

      newParamElement?.scrollIntoView?.();
    },

    setParameterKey(parameter) {
      if (this.paramKeys.has(parameter)) {
        return;
      }
      this.paramKeys.set(parameter, guid(32));
    }
  },

  watch: {
    openingNewParam(openingNewParam) {
      if (!openingNewParam) {
        return;
      }

      clearInterval(this.scrollInterval);
      this.scrollInterval = setInterval(() => {
        try {
          this.scrollToNewParam();
        } finally {
          if (!this.openingNewParam) {
            clearInterval(this.scrollInterval);
            this.scrollInterval = null;
          }
        }
      }, 40);
    },

    openedPanel(newVal) {
      if (this.openingNewParam) {
        this.$nextTick(() => {
          this.openingNewParam = false;
        });
      }
    },

    snackbarVisible(val) {
      if (!val) {
        this.undoQueue = [];
      }
    },

    parameters: {
      immediate: true,
      deep: true,
      handler(parameters) {
        for (const parameter of parameters) {
          this.setParameterKey(parameter);
        }
      }
    }
  }
}
</script>

<style scoped>
.script-param-list {
  display: flex;
  flex-direction: column;
}

.add-param-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  border-top: 1px solid rgba(0, 0, 0, 0.12);
}

.add-param-item:hover {
  background-color: var(--hover-color);
}

.add-param-item i {
  margin-right: 8px;
}
</style>

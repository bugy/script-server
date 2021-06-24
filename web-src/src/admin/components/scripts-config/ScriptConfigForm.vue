<template>
  <form class="script-config-form col">
    <div class="row">
      <TextField v-model="newName" :config="nameField" class="col s6"/>
      <TextField v-model="group" :config="groupField" class="col s5 offset-s1"/>
    </div>
    <div class="row">
      <ScriptPathField :config-name="newName" :new-config="isNew" :original-path="value['script_path']"
                       class="col s6" @change="updateScript"/>
      <TextField v-model="workingDirectory" :config="workDirField" class="col s5 offset-s1"/>
    </div>
    <div class="row">
      <TextArea v-model="description" :config="descriptionField" class="col s12"/>
    </div>
    <div class="row">
      <div v-if="allowAllUsers" class="input-field col s9">
        <input id="allowed_users_disabled" disabled type="text" value="All users">
        <label class="active" for="allowed_users_disabled">Allowed users</label>
      </div>
      <ChipsList v-else v-model="allowedUsers" class="col s9" title="Allowed users"/>
      <CheckBox v-model="allowAllUsers" :config="allowAllField"
                class="col s2 offset-s1 checkbox-field"/>
    </div>

    <div class="row">
      <div v-if="allowAllAdmins" class="input-field col s9">
        <input id="admin_users_disabled" disabled type="text" value="Any admin">
        <label class="active" for="admin_users_disabled">Admin users</label>
      </div>
      <ChipsList v-else v-model="adminUsers" class="col s9" title="Admin users"/>
      <CheckBox v-model="allowAllAdmins" :config="allowAllAdminsField"
                class="col s2 offset-s1 checkbox-field"/>
    </div>

    <div class="row">
      <Combobox v-model="outputFormat" :config="outputFormatField" class="col s3"/>
      <CheckBox v-model="requiresTerminal" :config="requiresTerminalField"
                class="col s3 checkbox-field"/>
      <TextField v-model="includeScript" :config="includeScriptField" class="col s5 offset-s1"/>
    </div>
  </form>
</template>

<script>
import CheckBox from '@/common/components/checkbox';
import ChipsList from '@/common/components/ChipsList';
import TextArea from '@/common/components/TextArea';
import TextField from '@/common/components/textfield'
import {forEachKeyValue, isEmptyArray, isEmptyString, isNull} from '@/common/utils/common';
import get from 'lodash/get';
import {
  allowAllField,
  descriptionField,
  groupField,
  includeScriptField,
  nameField,
  outputFormatField,
  requiresTerminalField,
  scriptPathField,
  workDirField
} from './script-fields';
import {allowAllAdminsField} from '@/admin/components/scripts-config/script-fields';
import Combobox from '@/common/components/combobox'
import ScriptPathField from '@/admin/components/scripts-config/script-edit/ScriptField'
import {NEW_SCRIPT} from '@/admin/store/script-config-module'


export default {
  name: 'ScriptConfigForm',
  components: {ScriptPathField, Combobox, TextArea, ChipsList, TextField, CheckBox},

  props: {
    value: {
      type: Object,
      default: null
    },
    originalName: String
  },

  data() {
    return {
      isNew: this.originalName === NEW_SCRIPT,
      newName: null,
      group: null,
      script: null,
      description: null,
      workingDirectory: null,
      requiresTerminal: null,
      includeScript: null,
      outputFormat: null,
      allowedUsers: [],
      allowAllUsers: true,
      adminUsers: [],
      allowAllAdmins: true,
      nameField,
      groupField,
      scriptPathField,
      workDirField,
      descriptionField,
      allowAllField,
      allowAllAdminsField,
      outputFormatField,
      requiresTerminalField,
      includeScriptField
    }
  },

  mounted: function () {
    const simpleFields = {
      'newName': 'name',
      'group': 'group',
      'description': 'description',
      'workingDirectory': 'working_directory',
      'requiresTerminal': 'requires_terminal',
      'includeScript': 'include',
      'outputFormat': 'output_format'
    };

    forEachKeyValue(simpleFields, (vmField, configField) => {
      this.$watch(vmField, (newValue) => {
        if (isNull(newValue) || isEmptyString(newValue)) {
          this.$delete(this.value, configField);
        } else {
          this.$set(this.value, configField, newValue);
        }
      });
    });
  },

  watch: {
    value: {
      immediate: true,
      handler(config) {
        this.newName = config.name;
        this.group = config.group;
        this.description = config['description'];
        this.workingDirectory = config['working_directory'];
        this.requiresTerminal = get(config, 'requires_terminal', true);
        this.includeScript = config['include'];
        this.outputFormat = config['output_format'];
        this.updateAccessFieldInVm(config,
            'allowedUsers',
            'allowAllUsers',
            'allowed_users')

        this.updateAccessFieldInVm(config,
            'adminUsers',
            'allowAllAdmins',
            'admin_users')
      }
    },
    allowAllUsers() {
      this.updateAllowedUsers();
    },
    allowedUsers() {
      this.updateAllowedUsers();
    },
    allowAllAdmins() {
      this.updateAdminUsers();
    },
    adminUsers() {
      this.updateAdminUsers();
    }
  },

  methods: {
    updateScript(newScriptObject) {
      this.value['script'] = newScriptObject
    },
    updateAllowedUsers() {
      this.updateAccessFieldInValue(this.allowAllUsers, 'allowedUsers', 'allowed_users');
    },
    updateAdminUsers() {
      this.updateAccessFieldInValue(this.allowAllAdmins, 'adminUsers', 'admin_users');
    },
    updateAccessFieldInValue(allowAll, vmPropertyName, valuePropertyName) {
      const newValue = this[vmPropertyName];

      if (isEmptyArray(newValue)) {
        this.$delete(this.value, valuePropertyName);
      } else {
        if (allowAll) {
          if (newValue.includes('*')) {
            this.value[valuePropertyName] = newValue;
          } else {
            this.value[valuePropertyName] = [...newValue, '*'];
          }
        } else {
          this.value[valuePropertyName] = newValue;
        }
      }
    },
    updateAccessFieldInVm(config, vmPropertyName, vmAllowAllPropertyName, valuePropertyName) {
      let users = get(config, valuePropertyName);
      if (isNull(users)) {
        users = [];
      }
      this[vmPropertyName] = users.filter(u => u !== '*');
      this[vmAllowAllPropertyName] = isNull(config[valuePropertyName]) || users.includes('*');
    }
  }
}
</script>

<style scoped>
.col.checkbox-field {
  margin-top: 2.1em;
}

.script-config-form .row {
  margin-bottom: 0;
  margin-left: 0;
  margin-right: 0;
}
</style>
<template>
  <form class="script-config-form col">
    <div class="row">
      <TextField v-model="newName" :config="nameField" class="col s6"/>
      <TextField v-model="group" :config="groupField" class="col s5 offset-s1"/>
    </div>
    <div class="row">
      <TextField v-model="scriptPath" :config="scriptPathField" class="col s6"/>
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
      <CheckBox v-model="bashFormatting" :config="bashFormattingField" class="col s3 checkbox-field"/>
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
  bashFormattingField,
  descriptionField,
  groupField,
  includeScriptField,
  nameField,
  requiresTerminalField,
  scriptPathField,
  workDirField
} from './script-fields';
import {allowAllAdminsField} from "@/admin/components/scripts-config/script-fields";

export default {
  name: 'ScriptConfigForm',
  components: {TextArea, ChipsList, TextField, CheckBox},

  props: {
    value: {
      type: Object,
      default: null
    }
  },

  data() {
    return {
      configCopy: null,
      newName: null,
      group: null,
      scriptPath: null,
      description: null,
      workingDirectory: null,
      requiresTerminal: null,
      includeScript: null,
      bashFormatting: null,
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
      bashFormattingField,
      requiresTerminalField,
      includeScriptField
    }
  },

  mounted: function () {
    const simpleFields = {
      'newName': 'name',
      'group': 'group',
      'scriptPath': 'script_path',
      'description': 'description',
      'workingDirectory': 'working_directory',
      'requiresTerminal': 'requires_terminal',
      'includeScript': 'include',
      'bashFormatting': 'bash_formatting'
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
        this.scriptPath = config['script_path'];
        this.description = config['description'];
        this.workingDirectory = config['working_directory'];
        this.requiresTerminal = get(config, 'requires_terminal', true);
        this.includeScript = config['include'];
        this.bashFormatting = get(config, 'bash_formatting', true);
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
    },

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
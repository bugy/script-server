<template>
    <form class="script-config-form col">
        <div class="row">
            <TextField :config="nameField" class="col s6" v-model="newName"/>
        </div>
        <div class="row">
            <TextField :config="scriptPathField" class="col s6" v-model="scriptPath"/>
            <TextField :config="workDirField" class="col s5 offset-s1" v-model="workingDirectory"/>
        </div>
        <div class="row">
            <TextArea :config="descriptionField" class="col s12" v-model="description"/>
        </div>
        <div class="row">
            <div class="input-field col s9" v-if="allowAllUsers">
                <input disabled id="allowed_users_disabled" type="text" value="All users">
                <label class="active" for="allowed_users_disabled">Allowed users</label>
            </div>
            <ChipsList class="col s9" title="Allowed users" v-else v-model="allowedUsers"/>
            <CheckBox :config="allowAllField" class="col s2 offset-s1 checkbox-field"
                      v-model="allowAllUsers"/>
        </div>

        <div class="row">
            <CheckBox :config="bashFormattingField" class="col s3 checkbox-field" v-model="bashFormatting"/>
            <CheckBox :config="requiresTerminalField" class="col s3 checkbox-field"
                      v-model="requiresTerminal"/>
            <TextField :config="includeScriptField" class="col s5 offset-s1" v-model="includeScript"/>
        </div>
    </form>
</template>

<script>
    import _ from 'lodash';
    import {forEachKeyValue, isEmptyArray, isEmptyString, isNull} from '../../common';
    import CheckBox from '../../components/checkbox'
    import TextArea from '../../components/TextArea';
    import TextField from '../../components/textfield'
    import ChipsList from '../../components/ChipsList';
    import {
        allowAllField,
        bashFormattingField,
        descriptionField,
        includeScriptField,
        nameField,
        requiresTerminalField,
        scriptPathField,
        workDirField
    } from './script-fields';

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
                scriptPath: null,
                description: null,
                workingDirectory: null,
                requiresTerminal: null,
                includeScript: null,
                bashFormatting: null,
                allowedUsers: [],
                allowAllUsers: true,
                nameField,
                scriptPathField,
                workDirField,
                descriptionField,
                allowAllField,
                bashFormattingField,
                requiresTerminalField,
                includeScriptField
            }
        },

        mounted: function () {
            const simpleFields = {
                'newName': 'name',
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
                    this.scriptPath = config['script_path'];
                    this.description = config['description'];
                    this.workingDirectory = config['working_directory'];
                    this.requiresTerminal = _.get(config, 'requires_terminal', true);
                    this.includeScript = config['include'];
                    this.bashFormatting = _.get(config, 'bash_formatting', true);
                    let allowedUsers = _.get(config, 'allowed_users');
                    if (isNull(allowedUsers)) {
                        allowedUsers = [];
                    }
                    this.allowedUsers = allowedUsers.filter(u => u !== '*');
                    this.allowAllUsers = isNull(config['allowed_users']) || allowedUsers.includes('*');
                }
            },
            allowAllUsers() {
                this.updateAllowedUsers();
            },
            allowedUsers() {
                this.updateAllowedUsers();
            }
        },

        methods: {
            updateAllowedUsers() {
                if (this.allowAllUsers) {
                    if (isEmptyArray(this.allowedUsers)) {
                        this.$delete(this.value, 'allowed_users');
                    } else {
                        if (this.allowedUsers.includes('*')) {
                            this.value['allowed_users'] = this.allowedUsers;
                        } else {
                            this.value['allowed_users'] = [...this.allowedUsers, '*'];
                        }
                    }
                } else {
                    this.value['allowed_users'] = this.allowedUsers;
                }
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
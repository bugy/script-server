<template>
    <div :id="id" class="script-view">
        <ScriptLoadingText :loading="loading" :script="selectedScript" v-if="loading"/>
        <p class="script-description" v-html="formattedDescription" v-show="scriptDescription"/>
        <ScriptParametersView ref="parametersView"/>
        <div class="actions-panel">
            <button class="button-execute btn"
                    :disabled="!enableExecuteButton"
                    v-bind:class="{ disabled: !enableExecuteButton }"
                    @click="executeScript">
                Execute
            </button>
            <button class="button-stop btn"
                    :disabled="!enableStopButton"
                    v-bind:class="{
                    disabled: !enableStopButton,
                    'red lighten-1': !killEnabled,
                    'grey darken-4': killEnabled}"
                    @click="stopScript">
                {{stopButtonLabel}}
            </button>
        </div>
        <LogPanel ref="logPanel" v-show="showLog && !hasErrors && !hideExecutionControls"/>
        <div class="validation-panel" v-if="hasErrors" v-show="!hideExecutionControls">
            <h6 class="header">Validation failed. Errors list:</h6>
            <ul class="validation-errors-list">
                <li v-for="error in errors">{{ error }}</li>
            </ul>
        </div>
        <div class="files-download-panel" v-if="downloadableFiles && (downloadableFiles.length > 0)"
             v-show="!hideExecutionControls">
            <a v-for="file in downloadableFiles"
               class="waves-effect waves-teal btn-flat"
               :download="file.filename"
               :href="file.url"
               target="_blank">
                {{ file.filename }}
                <img :src="downloadIcon">
            </a>
        </div>
        <div class="script-input-panel input-field" v-if="inputPromptText" v-show="!hideExecutionControls">
            <label class="script-input-label" :for="'inputField-' + id">{{ inputPromptText }}</label>
            <input class="script-input-field" type="text"
                   :id="'inputField-' + id"
                   ref="inputField"
                   v-on:keyup="inputKeyUpHandler">
        </div>
    </div>
</template>

<script>

    import FileDownloadIcon from '@/assets/file_download.png'
    import LogPanel from '@/common/components/log_panel'
    import {deepCloneObject, forEachKeyValue, isEmptyObject, isEmptyString, isNull} from '@/common/utils/common';
    import ScriptLoadingText from '@/main-app/components/scripts/ScriptLoadingText';
    import marked from 'marked';
    import {mapActions, mapState} from 'vuex'
    import {STATUS_DISCONNECTED, STATUS_ERROR, STATUS_EXECUTING, STATUS_FINISHED} from '../../store/scriptExecutor';
    import ScriptParametersView from './script-parameters-view'

    export default {
        data: function () {
            return {
                id: null,
                everStarted: false,
                errors: [],
                nextLogIndex: 0,
                lastInlineImages: {},
                downloadIcon: FileDownloadIcon
            }
        },

        props: {
            hideExecutionControls: Boolean
        },

        mounted: function () {
            this.id = 'script-panel-' + this._uid;
        },

        components: {
            ScriptLoadingText,
            LogPanel,
            ScriptParametersView
        },

        computed: {
            ...mapState('scriptConfig', {
                scriptDescription: state => state.scriptConfig ? state.scriptConfig.description : '',
                loading: 'loading'
            }),
            ...mapState('scriptSetup', {
                parameterErrors: 'errors'
            }),
            ...mapState('executions', {
                currentExecutor: 'currentExecutor'
            }),
            ...mapState('scripts', ['selectedScript']),

            hasErrors: function () {
                return !isNull(this.errors) && (this.errors.length > 0);
            },

            formattedDescription: function () {
                if (isEmptyString(this.scriptDescription)) {
                    return '';
                }

                var descriptionHtml = marked(this.scriptDescription, {sanitize: true, gfm: true, breaks: true});
                var paragraphRemoval = document.createElement('div');
                paragraphRemoval.innerHTML = descriptionHtml.trim();

                for (var i = 0; i < paragraphRemoval.childNodes.length; i++) {
                    var child = paragraphRemoval.childNodes[i];
                    if (child.tagName === 'P') {
                        i += child.childNodes.length - 1;

                        while (child.childNodes.length > 0) {
                            paragraphRemoval.insertBefore(child.firstChild, child);
                        }

                        paragraphRemoval.removeChild(child);
                    }
                }

                return paragraphRemoval.innerHTML;
            },

            enableExecuteButton() {
                if (this.hideExecutionControls) {
                    return false;
                }

                if (this.loading) {
                    return false;
                }

                if (isNull(this.currentExecutor)) {
                    return true;
                }

                return this.currentExecutor.state.status === STATUS_FINISHED
                    || this.currentExecutor.state.status === STATUS_DISCONNECTED
                    || this.currentExecutor.state.status === STATUS_ERROR;
            },

            enableStopButton() {
                return this.status === STATUS_EXECUTING;
            },

            stopButtonLabel() {
                if (this.status === STATUS_EXECUTING) {
                    if (this.killEnabled) {
                        return 'Kill';
                    }

                    if (!isNull(this.killEnabledTimeout)) {
                        return 'Stop (' + this.killEnabledTimeout + ')';
                    }
                }

                return 'Stop';
            },

            status() {
                return isNull(this.currentExecutor) ? null : this.currentExecutor.state.status;
            },

            showLog() {
                return !isNull(this.currentExecutor);
            },

            downloadableFiles() {
                if (!this.currentExecutor) {
                    return [];
                }

                return this.currentExecutor.state.downloadableFiles;
            },

            inlineImages() {
                if (!this.currentExecutor) {
                    return {};
                }

                return this.currentExecutor.state.inlineImages;
            },

            inputPromptText() {
                if (this.status !== STATUS_EXECUTING) {
                    return null;
                }

                return this.currentExecutor.state.inputPromptText;
            },

            logChunks() {
                if (!this.currentExecutor) {
                    return [];
                }

                return this.currentExecutor.state.logChunks;
            },

            killEnabled() {
                return !isNull(this.currentExecutor) && this.currentExecutor.state.killEnabled;
            },

            killEnabledTimeout() {
                return isNull(this.currentExecutor) ? null : this.currentExecutor.state.killTimeoutSec;
            }
        },

        methods: {
            inputKeyUpHandler: function (event) {
                if (event.keyCode === 13) {
                    const inputField = this.$refs.inputField;

                    this.sendUserInput(inputField.value);

                    inputField.value = '';
                }
            },

            executeScript: function () {
                this.errors = [];

                const errors = this.parameterErrors;
                if (!isEmptyObject(errors)) {
                    forEachKeyValue(errors, (paramName, error) => {
                        this.errors.push(paramName + ': ' + error);
                    });
                    return;
                }

                this.startExecution();
            },

            ...mapActions('executions', {
                startExecution: 'startExecution'
            }),

            stopScript() {
                if (isNull(this.currentExecutor)) {
                    return;
                }

                if (this.killEnabled) {
                    this.$store.dispatch('executions/' + this.currentExecutor.state.id + '/killExecution');
                } else {
                    this.$store.dispatch('executions/' + this.currentExecutor.state.id + '/stopExecution');
                }
            },

            sendUserInput(value) {
                if (isNull(this.currentExecutor)) {
                    return;
                }

                this.$store.dispatch('executions/' + this.currentExecutor.state.id + '/sendUserInput', value);
            },

            setLog: function (text) {
                this.$refs.logPanel.setLog(text);
            },

            appendLog: function (text) {
                this.$refs.logPanel.appendLog(text);
            }
        },

        watch: {
            inputPromptText: function (value) {
                if (isNull(value) && isNull(this.$refs.inputField)) {
                    return;
                }

                var fieldUpdater = function () {
                    this.$refs.inputField.value = '';
                    if (!isNull(value)) {
                        this.$refs.inputField.focus();
                    }
                }.bind(this);

                if (this.$refs.inputField) {
                    fieldUpdater();
                } else {
                    this.$nextTick(fieldUpdater);
                }
            },

            logChunks: {
                handler(newValue, oldValue) {
                    if (isNull(newValue)) {
                        this.setLog('');
                        this.nextLogIndex = 0;

                        return;
                    }

                    if (newValue !== oldValue) {
                        this.setLog('');
                        this.nextLogIndex = 0;
                    }

                    for (; this.nextLogIndex < newValue.length; this.nextLogIndex++) {
                        const logChunk = newValue[this.nextLogIndex];

                        this.appendLog(logChunk);
                    }
                }
            },

            inlineImages: {
                handler(newValue, oldValue) {
                    const logPanel = this.$refs.logPanel;

                    forEachKeyValue(this.lastInlineImages, (key, value) => {
                        if (!newValue.hasOwnProperty(key)) {
                            logPanel.removeInlineImage(key);
                        } else if (value !== newValue[key]) {
                            logPanel.setInlineImage(key, value);
                        }
                    });

                    forEachKeyValue(newValue, (key, value) => {
                        if (!this.lastInlineImages.hasOwnProperty(key)) {
                            logPanel.setInlineImage(key, value);
                        }
                    });

                    this.lastInlineImages = deepCloneObject(newValue);
                }
            }
        }
    }
</script>

<style scoped>

    .script-view {
        display: flex;
        flex-direction: column;
        flex: 1 1 0;


        /* (firefox)
            we have to specify min-size explicitly, because by default it's content size.
            It means, that when child content is larger than parent, it will grow out of parent
            See https://drafts.csswg.org/css-flexbox/#min-size-auto
            and https://bugzilla.mozilla.org/show_bug.cgi?id=1114904
        */
        min-height: 0;
    }

    .script-view >>> .script-parameters-panel,
    .actions-panel,
    .files-download-panel {
        flex: 0 0 content;
    }

    .script-description,
    .script-loading-text {
        margin: 0;
    }

    .actions-panel {
        display: flex;
    }

    .button-execute {
        flex: 6 1 5em;

        margin-right: 0;
        margin-top: 6px;
    }

    .button-stop {
        flex: 1 0 5em;

        margin-left: 12px;
        margin-top: 6px;
    }

    .script-input-panel {
        margin-top: 20px;
        margin-bottom: 0;
    }

    .script-input-panel input[type=text] {
        margin: 0;
        width: 100%;
        height: 1.5em;
        font-size: 1rem;
    }

    .script-input-panel > label {
        transform: translateY(-30%);
        margin-left: 2px;
    }

    .script-input-panel.input-field > label.active {
        color: #26a69a;
        transform: translateY(-70%) scale(0.8);
    }

    .validation-panel {
        overflow-y: auto;
        flex: 1;

        margin: 17px 12px 7px;
    }

    .validation-errors-list {
        margin-left: 17px;
    }

    .validation-errors-list li {
        color: #F44336;
    }

    .files-download-panel {
        margin-top: 12px;
    }

    .files-download-panel a {
        color: #26a69a;
        padding-left: 16px;
        padding-right: 16px;
        margin-right: 8px;
        text-transform: none;
    }

    .files-download-panel a > img {
        width: 12px;
        margin-left: 10px;
        vertical-align: middle;
    }

    .script-view >>> .log-panel {
        margin-top: 12px;
    }

</style>

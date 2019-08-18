<template>
    <div :id="id" class="script-view">
        <p class="script-description" v-show="scriptDescription" v-html="formattedDescription"></p>
        <ScriptParametersView ref="parametersView"/>
        <div>
            <button class="button-execute btn"
                    :disabled="!enableExecuteButton"
                    v-bind:class="{ disabled: !enableExecuteButton }"
                    @click="executeScript">
                Execute
            </button>
            <button class="button-stop btn red lighten-1"
                    :disabled="!enableStopButton"
                    v-bind:class="{ disabled: !enableStopButton}"
                    @click="stopScript">
                Stop
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
                <img src="images/file_download.png">
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

    import marked from 'marked';
    import {mapActions, mapState} from 'vuex'
    import {forEachKeyValue, isEmptyObject, isEmptyString, isNull} from '../common';
    import LogPanel from '../components/log_panel'
    import {
        STATUS_DISCONNECTED,
        STATUS_ERROR,
        STATUS_EXECUTING,
        STATUS_FINISHED
    } from '../main-app/store/scriptExecutor';
    import ScriptParametersView from './script-parameters-view'

    export default {
        data: function () {
            return {
                id: null,
                everStarted: false,
                errors: [],
                nextLogIndex: 0
            }
        },

        props: {
            hideExecutionControls: Boolean
        },

        mounted: function () {
            this.id = 'script-panel-' + this._uid;
        },

        components: {
            LogPanel, ScriptParametersView
        },

        computed: {
            ...mapState('scriptConfig', {
                scriptDescription: state => state.scriptConfig ? state.scriptConfig.description : ''
            }),
            ...mapState('scriptSetup', {
                parameterErrors: 'errors'
            }),
            ...mapState('executions', {
                currentExecutor: 'currentExecutor'
            }),

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
                if (isNull(this.currentExecutor)) {
                    return true;
                }

                return this.currentExecutor.state.status === STATUS_FINISHED
                    || this.currentExecutor.state.status === STATUS_DISCONNECTED
                    || this.currentExecutor.state.status === STATUS_ERROR;
            },

            enableStopButton() {
                return !isNull(this.currentExecutor) && this.currentExecutor.state.status === STATUS_EXECUTING;
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

            inputPromptText() {
                if (isNull(this.currentExecutor) || (this.currentExecutor.state.status !== STATUS_EXECUTING)) {
                    return null;
                }

                return this.currentExecutor.state.inputPromptText;
            },

            logChunks() {
                if (!this.currentExecutor) {
                    return [];
                }

                return this.currentExecutor.state.logChunks;
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

                this.$store.dispatch('executions/' + this.currentExecutor.state.id + '/stopExecution');
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
            }
        }
    }
</script>

<style scoped>

    .script-view {
        display: flex;
        flex-direction: column;
        flex: 1 1 auto;


        /* (firefox)
            we have to specify min-size explicitly, because by default it's content size.
            It means, that when child content is larger than parent, it will grow out of parent
            See https://drafts.csswg.org/css-flexbox/#min-size-auto
            and https://bugzilla.mozilla.org/show_bug.cgi?id=1114904
        */
        min-height: 0;
    }

    .script-description {
        margin: 15px 17px 0;
    }

    .button-execute {
        width: 80%;
        margin-left: 2%;
        margin-right: 0;
        margin-top: 6px;
        display: inline;
    }

    .button-stop {
        width: calc(96% - 80% - 12px - 5px); /* width without margins - executeButton - margin between button - rounding error */
        margin-left: 12px;
        margin-right: 2%;
        margin-top: 6px;
        display: inline;
    }

    .script-input-panel {
        width: calc(100% - 24px);
        margin: 18px 12px 0;
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
        margin: 12px 12px 0;
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
        margin-right: 12px;
        margin-left: 12px;
        width: calc(100% - 24px);
        margin-top: 12px;
    }

</style>

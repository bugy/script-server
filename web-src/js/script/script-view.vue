<template>
    <div class="script-panel" :id="id">
        <p class="script-description" v-show="scriptDescription" v-html="formattedDescription"></p>
        <ScriptParametersView ref="parametersView"/>
        <div>
            <button class="button-execute btn"
                    :disabled="executing"
                    v-bind:class="{ disabled: executing }"
                    @click="executeScript">
                Execute
            </button>
            <button class="button-stop btn red lighten-1"
                    :disabled="!executing"
                    v-bind:class="{ disabled: !executing}"
                    @click="stopScript">
                Stop
            </button>
        </div>
        <LogPanel ref="logPanel" v-show="everStarted && !hasErrors"/>
        <div class="validation-panel" v-if="hasErrors">
            <h6 class="header">Validation failed. Errors list:</h6>
            <ul class="validation-errors-list">
                <li v-for="error in errors">{{ error }}</li>
            </ul>
        </div>
        <div class="files-download-panel" v-if="downloadableFiles && (downloadableFiles.length > 0)">
            <a v-for="file in downloadableFiles"
               class="waves-effect waves-teal btn-flat"
               :download="file.filename"
               :href="file.url"
               target="_blank">
                {{ file.filename }}
                <img src="images/file_download.png">
            </a>
        </div>
        <div class="script-input-panel input-field" v-if="inputPromptText">
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
    import {forEachKeyValue, isEmptyObject, isEmptyString, isNull, toBoolean} from '../common';
    import LogPanel from '../components/log_panel'
    import ScriptParametersView from './script-parameters-view'
    import {RESET_DOWNLOADABLE_FILES, SEND_USER_INPUT, START_EXECUTION, STOP_EXECUTION} from './vuex_constants';

    export default {
        data: function () {
            return {
                id: null,
                everStarted: false,
                errors: [],
                nextLogIndex: 0
            }
        },

        mounted: function () {
            this.id = 'script-panel-' + this._uid;
        },

        components: {
            LogPanel, ScriptParametersView
        },

        computed: {
            ...mapState({
                scriptDescription: state => state.scriptConfig ? state.scriptConfig.description : '',
                executing: 'executing',
                downloadableFiles: 'downloadableFiles',
                inputPromptText: 'inputPromptText',
                logChunks: 'logChunks'
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
                this.$store.commit(RESET_DOWNLOADABLE_FILES);

                var errors = this.$refs.parametersView.getErrors();
                if (!isEmptyObject(errors)) {
                    forEachKeyValue(errors, (paramName, error) => {
                        this.errors.push(paramName + ': ' + error);
                    });
                    return;
                }

                this.$store.dispatch(START_EXECUTION);
            },

            ...mapActions({
                stopScript: STOP_EXECUTION,
                sendUserInput: SEND_USER_INPUT
            }),

            setLog: function (text) {
                this.$refs.logPanel.setLog(text);
            },

            appendLog: function (text, textColor, backgroundColor, textStyles) {
                this.$refs.logPanel.appendLog(text, textColor, backgroundColor, textStyles);
            },

            replaceLog: function (text, textColor, backgroundColor, textStyles, x, y) {
                this.$refs.logPanel.replaceLog(text, textColor, backgroundColor, textStyles, x, y);
            },

            getParameterErrors: function () {
                return this.$refs.parametersView.getErrors();
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

            executing: function (value) {
                const newExecuting = toBoolean(value);

                if (newExecuting) {
                    this.errors = [];

                    if (!this.everStarted) {
                        this.everStarted = true;
                    }
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

                        var text = logChunk.text;
                        var textColor = logChunk.text_color;
                        var backgroundColor = logChunk.background_color;
                        var textStyles = logChunk.text_styles;

                        if (toBoolean(logChunk.replace)) {
                            this.replaceLog(text, textColor, backgroundColor, textStyles, logChunk.custom_position.x, logChunk.custom_position.y);
                        } else {
                            this.appendLog(text, textColor, backgroundColor, textStyles);
                        }

                    }
                }
            }
        }
    }
</script>

<style scoped>

</style>

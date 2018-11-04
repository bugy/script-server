import marked from 'marked';
import Vue from 'vue';
import {forEachKeyValue, guid, isEmptyObject, isEmptyString, isNull} from '../common';

export function ScriptView(parent, parametersState) {
    var idSuffix = guid(8);

    var vueApp = document.createElement('div');
    vueApp.id = 'script-panel-' + idSuffix;
    vueApp.className = 'script-panel';
    parent.appendChild(vueApp);

    this.vueModel = new Vue({
        el: "#" + vueApp.id,

        template:
            '<div class="script-panel" :id="id">\n'
            + ' <p class="script-description" v-show="scriptDescription" v-html="formattedDescription"></p>\n'
            + ' <script-parameters-view :parametersState="parametersState" ref="parametersView" />\n'
            + ' <div>\n'
            + '     <button class="button-execute btn"'
            + '         :disabled="!executeEnabled"'
            + '         v-bind:class="{ disabled: !executeEnabled}"'
            + '         @click="executeButtonHandler()">'
            + '         Execute'
            + '     </button>\n'
            + '     <button class="button-stop btn red lighten-1" '
            + '         :disabled="!stopEnabled"'
            + '         v-bind:class="{ disabled: !stopEnabled}"'
            + '         @click="stopButtonHandler()">'
            + '         Stop'
            + '     </button>\n'
            + ' </div>\n'
            + ' <log-panel ref="logPanel" v-show="everStarted && !hasErrors"/>\n'
            + ' <div class="validation-panel" v-if="hasErrors">\n'
            + '     <h6 class="header">Validation failed. Errors list:</h6>\n'
            + '     <ul class="validation-errors-list">'
            + '         <li v-for="error in errors">{{ error }}</li>'
            + '     </ul>\n'
            + ' </div>\n'
            + ' <div class="files-download-panel" v-if="downloadableFiles && (downloadableFiles.length > 0)">'
            + '     <a v-for="file in downloadableFiles"'
            + '         class="waves-effect waves-teal btn-flat"'
            + '         :download="file.filename"'
            + '         :href="file.url"'
            + '         target="_blank">'
            + '         {{ file.filename }}'
            + '         <img src="images/file_download.png">'
            + '     </a>'
            + ' </div>\n'
            + ' <div class="script-input-panel input-field" v-if="inputPrompt">\n'
            + '    <label class="script-input-label" for="inputField-' + idSuffix + '">{{ inputPrompt.text }}</label>\n'
            + '    <input class="script-input-field" type="text" '
            + '         id="inputField-' + idSuffix + '"'
            + '         ref="inputField"'
            + '         v-on:keyup="inputKeyUpHandler">\n'
            + ' </div>\n' +
            '</div>',

        data: function () {
            return {
                id: null,
                executeEnabled: true,
                stopEnabled: false,
                parametersState: parametersState.state
            }
        },

        computed: {
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
                    var inputField = this.$refs.inputField;

                    this.inputPrompt.callback(inputField.value);

                    inputField.value = '';
                }
            }
        },

        mounted: function () {
            this.id = 'script-panel-' + guid(8);
        },

        watch: {
            inputPrompt: function (value) {
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
            }
        },

        props: {
            executeButtonHandler: Function,
            stopButtonHandler: Function,
            errors: Array,
            downloadableFiles: {
                type: Array,
                default: function () {
                    return []
                }
            },
            scriptDescription: {
                type: String,
                default: ''
            },
            everStarted: Boolean,
            log: {
                type: String,
                default: ''
            },
            inputPrompt: Object
        }
    });

    this.vueModel.executeButtonHandler = this._executeButtonHandler.bind(this);
    this.executionCallback = function () {
    };
}

ScriptView.prototype.setScriptDescription = function (description) {
    this.vueModel.scriptDescription = description;
};

ScriptView.prototype.getParameterErrors = function () {
    return this.vueModel.$refs.parametersView.getErrors();
};

ScriptView.prototype.destroy = function () {
    this.vueModel.$destroy();
};

ScriptView.prototype.setExecutionCallback = function (callback) {
    this.executionCallback = callback;
};

ScriptView.prototype.setStopCallback = function (callback) {
    this.vueModel.stopButtonHandler = callback;
};

ScriptView.prototype._executeButtonHandler = function () {
    var vueModel = this.vueModel;

    vueModel.errors = [];
    vueModel.downloadableFiles = [];

    var errors = vueModel.$refs.parametersView.getErrors();
    if (!isEmptyObject(errors)) {
        forEachKeyValue(errors, function (paramName, error) {
            vueModel.errors.push(paramName + ': ' + error);
        });
        return;
    }

    this.executionCallback();
};

ScriptView.prototype.setExecutionEnabled = function (enabled) {
    this.vueModel.executeEnabled = enabled;
};

ScriptView.prototype.setStopEnabled = function (enabled) {
    this.vueModel.stopEnabled = enabled;
};

ScriptView.prototype.setLog = function (text) {
    this.vueModel.$refs.logPanel.setLog(text);
};

ScriptView.prototype.appendLog = function (text, textColor, backgroundColor, textStyles) {
    this.vueModel.$refs.logPanel.appendLog(text, textColor, backgroundColor, textStyles);
};

ScriptView.prototype.replaceLog = function (text, textColor, backgroundColor, textStyles, x, y) {
    this.vueModel.$refs.logPanel.replaceLog(text, textColor, backgroundColor, textStyles, x, y);
};

ScriptView.prototype.setExecuting = function () {
    this.vueModel.everStarted = true;
    this.vueModel.executeEnabled = false;
    this.vueModel.stopEnabled = true;

    this.vueModel.errors = [];
};

ScriptView.prototype.showInputField = function (promptText, userInputCallback) {
    this.vueModel.inputPrompt = {'text': promptText, 'callback': userInputCallback};
};

ScriptView.prototype.hideInputField = function () {
    this.vueModel.inputPrompt = null;
};

ScriptView.prototype.addFileLink = function (url, filename) {
    this.vueModel.downloadableFiles.push({url: url, filename: filename});
};

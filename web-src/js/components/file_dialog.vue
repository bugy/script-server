<template>
    <div class="file-dialog"
         @keydown.down.prevent="selectNextFile(1)"
         @keydown.up.prevent="selectNextFile(-1)"
         @keypress.13.prevent="onEnterPressed($event)"
         @keyup.8="navigateUp(1)"
         @keypress.esc="onClose"
         @keypress="onKeyPressed($event)">
        <div class="file-dialog-header">
            <nav class="teal darken-4">
                <div class="nav-wrapper">
                    <div class="path-breadcrumbs">
                        <a href="#"
                           class="breadcrumb"
                           @click.prevent="openPath([])"><i class="material-icons">home</i></a>
                        <a href="#" class="breadcrumb" v-if="path.length > 3"
                           @click.prevent="navigateUp(2)">...</a>
                        <a v-for="(item, index) in path"
                           v-if="(path.length <= 3) || (index >= (path.length - 2))"
                           href="#"
                           class="breadcrumb"
                           @click.prevent="navigateUp(path.length - index - 1)">{{ item }}</a>
                    </div>
                </div>
            </nav>
        </div>
        <div class="file-dialog-content" tabindex="0" ref="contentPanel">
            <div class="loading-field" v-if="loading">Loading...</div>
            <ul class="collection" v-else-if="!error">
                <li class="collection-item"
                    :class="{ active: file === selectedFile }"
                    v-for="file in files"
                    @click="selectFile(file)"
                    v-on:dblclick="onFileAction(file)">
                    <i class="material-icons">{{ getIcon(file) }}</i>
                    <span>{{ file.name }}</span>
                </li>
            </ul>
            <div class="red-text load-error-field" v-else>{{error}}</div>
        </div>
        <div class="file-dialog-footer">
            <a class="waves-effect waves-teal btn-flat"
               @click="onClose">Cancel</a>
            <a class="waves-effect waves-teal btn-flat"
               @click="triggerFileChosen(null)">Clear</a>
            <a class="waves-effect waves-teal btn-flat"
               @click="triggerFileChosen(selectedFile)"
               :disabled="(selectedFile === null) || (!isChoosable(selectedFile))">Select</a>
        </div>
    </div>
</template>

<script>

    import {
        arraysEqual,
        isEmptyArray,
        isEmptyString,
        isNull,
        logError,
        scrollToElement,
        stringComparator
    } from '../common';

    export default {
        name: "file_dialog",
        props: {
            onClose: {
                type: Function
            },
            onFileSelect: {
                type: Function
            },
            loadFiles: {
                type: Function
            },
            fileType: {
                type: String
            },
            opened: {
                type: Boolean,
                default: true
            }
        },
        data() {
            return {
                selectedFile: null,
                path: [],
                files: [],
                error: null,
                loading: false
            }
        },
        watch: {
            opened: function (newValue) {
                if (newValue) {
                    this.openPath(this.path);
                }
            }
        },
        mounted: function () {
            if (this.opened) {
                this.openPath([]);
            }
        },
        methods: {
            focus() {
                this.$refs.contentPanel.focus();
            },

            setChosenFile(path) {
                let newPath;
                let selectedFilename;

                if (isEmptyArray(path)) {
                    newPath = [];
                    selectedFilename = null;
                } else {
                    newPath = path.slice(0, path.length - 1);
                    selectedFilename = path[path.length - 1];
                }

                if (this.opened) {
                    this.openPath(newPath, selectedFilename);
                } else {
                    this.selectedFile = selectedFilename ? {name: selectedFilename} : null;
                    this.path = newPath;
                }
            },

            getIcon(file) {
                if (file.type === 'dir') {
                    if (file.readable === false) {
                        return 'lock';
                    } else {
                        return 'folder'
                    }
                }

                return 'description';
            },

            isChoosable(file) {
                if (isEmptyString(this.fileType) || isNull(file)) {
                    return true;
                }

                return file.type === this.fileType;
            },

            selectFile(file) {
                this.selectedFile = file;

                if (isNull(file)) {
                    return;
                }

                this.$nextTick(() => {
                    const activeElement = $(this.$el).find('.file-dialog-content .active');
                    if (activeElement.length === 0) {
                        return;
                    }

                    scrollToElement(activeElement.get(0), true);
                });
            },

            onFileAction(file) {
                if (file.type === 'dir') {
                    if (file.readable !== false) {
                        this.openPath([...this.path, file.name]);
                    }
                } else {
                    this.triggerFileChosen(file);
                }
            },

            async openPath(path, fileToSelect) {
                try {
                    const samePath = arraysEqual(path, this.path);

                    if ((typeof fileToSelect) === 'undefined' && (samePath && !isNull(this.selectedFile))) {
                        fileToSelect = this.selectedFile.name;
                    }

                    this.path = path;
                    this.selectedFile = null;
                    this.loading = true;
                    this.error = null;

                    let children = await this.loadFiles(path);
                    if (isNull(children)) {
                        children = [];
                    }

                    if (this.path === path) {
                        children.sort(stringComparator('type').andThen(stringComparator('name')));
                        this.files = children;
                        this.loading = false;

                        if (!isNull(fileToSelect)) {
                            const selectedFile = this.files.find((f) => f.name === fileToSelect);
                            if (selectedFile) {
                                this.selectFile(selectedFile);
                            }
                        }
                    }

                } catch (e) {
                    if (this.path === path) {
                        this.error = 'Failed to load files';
                        this.files = [];
                        this.loading = false;
                    }

                    logError(e);
                }
            },

            triggerFileChosen(file) {
                if (!this.isChoosable(file)) {
                    return;
                }

                this.selectFile(file);

                if (isNull(file)) {
                    this.onFileSelect([]);
                } else {
                    this.onFileSelect([...this.path, file.name]);
                }
            },

            selectNextFile(direction = 1) {
                const step = direction >= 0 ? 1 : -1;

                const currentIndex = (this.selectedFile === null) ? -1 : this.files.indexOf(this.selectedFile);
                let nextIndex = currentIndex + step;
                if (nextIndex >= this.files.length) {
                    nextIndex = 0;
                } else if (nextIndex < 0) {
                    nextIndex = this.files.length - 1;
                }

                this.selectFile(this.files[nextIndex]);
            },

            onEnterPressed(event) {
                if (isNull(this.selectedFile)) {
                    return;
                }

                if ((event.ctrlKey) || (event.shiftKey)) {
                    this.triggerFileChosen(this.selectedFile);
                } else {
                    this.onFileAction(this.selectedFile);
                }
            },

            navigateUp(positions = 1) {
                if (isEmptyArray(this.path) || (positions > this.path.length)) {
                    return;
                }

                if (this.path.length === 1) {
                    this.openPath([]);
                } else {
                    this.openPath(this.path.slice(0, this.path.length - positions));
                }
            },

            onKeyPressed(event) {
                if (event.altKey || event.ctrlKey || event.metaKey) {
                    return;
                }

                const charCode = event.keyCode || event.which;
                const char = String.fromCharCode(charCode);

                if (!/\w/u.test(char)) {
                    return;
                }

                const lowerChar = char.toLowerCase();

                for (const file of this.files) {
                    if (!file.name.toLowerCase().startsWith(lowerChar)) {
                        continue;
                    }

                    this.selectFile(file);
                    break;
                }

                event.preventDefault();
            }
        }
    }
</script>

<style scoped>
    .file-dialog {
        width: 500px;
        height: 500px;
        display: flex;
        flex-direction: column;
        border: 1px solid #E0E0E0;
        border-radius: 2px;
    }

    .file-dialog-header {
        flex: none;
    }

    nav {
        height: 48px;
        padding: 12px 24px;
        box-shadow: none;
    }

    .nav-wrapper {
        line-height: initial;
    }

    .file-dialog-header .path-breadcrumbs {
        white-space: nowrap;
        max-width: calc(100% - 48px);
        overflow: hidden;
    }

    .file-dialog-header .breadcrumb {
        max-width: 100px;
        display: inline-block;

        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .file-dialog-header .breadcrumb:last-child {
        max-width: 200px;
    }

    .path-breadcrumbs a.breadcrumb {
        font-size: 16px;
        line-height: 24px;
    }

    .path-breadcrumbs a.breadcrumb:before {
        margin: 0 4px;
    }

    .file-dialog-header .breadcrumb > i {
        height: min-content;
        line-height: inherit;
    }

    .file-dialog-content {
        flex: 1 1 auto;
        overflow-y: auto;
        outline: none;
    }

    .file-dialog-footer {
        flex: none;
        text-align: right;
        border-top: 1px solid rgba(160, 160, 160, 0.2);
    }

    .file-dialog-content .collection {
        margin: 0;
        border: none;
    }

    .file-dialog-content .collection-item {
        background: none;
        border: none;
        vertical-align: middle;
        display: flex;
        align-items: center;
        cursor: pointer;
    }

    .file-dialog-content .collection-item:not(.active):hover {
        background-color: #ddd;
    }

    .file-dialog-content .collection-item * {
        -moz-user-select: none;
        -webkit-user-select: none;
        -ms-user-select: none;
        user-select: none;
    }

    .file-dialog-content .collection-item i {
        height: 30px;
        line-height: 30px;
        margin-right: 20px;
        color: #757575;
    }

    .file-dialog-content:not(:focus) .collection-item.active i {
        color: rgba(120, 120, 120, 0.87);
    }

    .file-dialog-content:not(:focus) .collection-item.active {
        background-color: rgba(0, 0, 0, 0.08);
        color: rgba(50, 50, 50, 0.87);
    }

    .file-dialog-content .collection-item.active i {
        color: #FFF;
    }

    .file-dialog-content .collection-item span {
        flex: 1 1 auto;
    }

    .load-error-field,
    .loading-field {
        margin: 16px;
    }

</style>
<template>
    <div class="scripts-list collection">
        <a :href="'#' + script.hash"
           class="collection-item waves-effect waves-teal"
           v-bind:class="{ active: script.active}"
           v-for="script in scriptDescriptors">
            {{ script.name }}

            <div :class="script.state" class="menu-item-state">
                <i class="material-icons check-icon">check</i>
                <div class="preloader-wrapper active">
                    <div class="spinner-layer">
                        <div class="circle-clipper left">
                            <div class="circle"></div>
                        </div>
                        <div class="gap-patch">
                            <div class="circle"></div>
                        </div>
                        <div class="circle-clipper right">
                            <div class="circle"></div>
                        </div>
                    </div>
                </div>
            </div>
        </a>
    </div>
</template>

<script>
    import {mapState} from 'vuex';
    import {forEachKeyValue, isEmptyString} from '../common';
    import {scriptNameToHash} from './model_helper';

    export default {
        name: 'ScriptsList',

        props: {
            searchText: {
                type: String,
                default: null
            }
        },

        computed: {
            ...mapState('scripts', {
                scripts: 'scripts',
                selectedScript: 'selectedScript'
            }),

            scriptDescriptors() {
                return this.scripts
                    .map(scriptName => {
                        return {
                            name: scriptName,
                            state: this.getState(scriptName),
                            active: this.selectedScript === scriptName,
                            hash: this.toHash(scriptName)
                        }
                    })
                    .filter(d =>
                        isEmptyString(this.searchText) || (d.name.toLowerCase().includes(this.searchText.toLowerCase())))
            }
        },
        methods: {
            toHash: scriptNameToHash,

            getState(scriptName) {
                let state = 'idle';

                forEachKeyValue(this.$store.state.executions.executors, function (id, executor) {
                    if (executor.state.scriptName !== scriptName) {
                        return;
                    }

                    state = executor.state.status;
                });

                return state;
            }
        }
    }
</script>

<style scoped>
    .scripts-list {
        overflow: auto;
        overflow-wrap: normal;
        border: none;
        margin: 0;

        flex-grow: 1;
    }

    .scripts-list .collection-item {
        border: none;
        padding-right: 32px;
    }

    .scripts-list .collection-item .menu-item-state {
        width: 24px;
        height: 24px;
        position: absolute;
        right: 8px;
        top: calc(50% - 12px);
        display: none;
    }

    .scripts-list .collection-item .menu-item-state > .check-icon {
        color: #26a69a;
        display: none;
        font-size: 24px;
    }

    .scripts-list .collection-item.active .menu-item-state > .check-icon {
        color: white;
    }

    .scripts-list .collection-item .menu-item-state > .preloader-wrapper {
        display: none;
        width: 100%;
        height: 100%;
    }

    .scripts-list .collection-item .menu-item-state.executing,
    .scripts-list .collection-item .menu-item-state.finished {
        display: inline;
    }

    .scripts-list .collection-item .menu-item-state.executing > .check-icon {
        display: none;
    }

    .scripts-list .collection-item .menu-item-state.executing > .preloader-wrapper {
        display: block;
    }

    .scripts-list .collection-item .menu-item-state.finished > .check-icon {
        display: block;
    }

    .scripts-list .collection-item .menu-item-state.finished > .preloader-wrapper {
        display: none;
    }

    .scripts-list .collection-item.active .preloader-wrapper .spinner-layer {
        border-color: white;
    }

    .scripts-list .collection-item .preloader-wrapper .spinner-layer {
        border-color: #26a69a;
    }

</style>
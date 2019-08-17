<template>
    <div class="main-app-content">
        <ScriptView :class="{collapsed: showError}" :hideExecutionControls="showError"
                    ref="scriptView"/>
        <div class="error-panel" v-if="showError">
            <p v-if="!authenticated">
                Credentials expired, please <a href="javascript:void(0)" onclick="location.reload()">relogin</a>
            </p>
            <p v-else-if="scriptLoadError">
                Failed to load script info. Try to reload the page. Error message:
                <br>
                {{ scriptLoadError }}
            </p>
        </div>
    </div>
</template>

<script>
    import {mapState} from 'vuex';
    import ScriptView from './script-view';

    export default {
        name: 'MainAppContent',
        components: {ScriptView},

        computed: {
            showError() {
                return !!(this.scriptLoadError || !this.authenticated);
            },
            ...mapState('auth', ['authenticated']),
            ...mapState('scriptConfig', {scriptLoadError: 'loadError'})
        }
    }
</script>

<style scoped>
    .main-app-content {
        height: 100%;

        background: white;
        padding-bottom: 12px;

        display: flex;
        flex-direction: column;
    }

    .main-app-content >>> .input-field label {
        top: 0;

        text-overflow: ellipsis;
        white-space: nowrap;
        overflow: hidden;
    }

    .collapsed {
        flex-grow: 0;
    }

    .error-panel {
        margin-left: 17px;
        color: #F44336;
        margin-top: 17px;
    }

    .error-panel p {
        margin: 0;
    }

    .main-app-content >>> .select-dropdown.dropdown-content li.disabled,
    .main-app-content >>> .select-dropdown.dropdown-content li.disabled > span,
    .main-app-content >>> .select-dropdown.dropdown-content li.optgroup {
        background-color: transparent;
    }

</style>
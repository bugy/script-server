<template>
    <div class="script-config">
        <div class="script-config-content" ref="scriptConfigContent">
            <div class="container">
                <div class="error" v-if="loadingError">{{ loadingError }}</div>
                <ScriptConfigForm v-else-if="scriptConfig" v-model="scriptConfig"/>
                <div v-if="!loadingError && scriptConfig">
                    <h5>Parameters</h5>
                    <ScriptParamList :parameters="scriptConfig.parameters"/>
                </div>
            </div>
        </div>
        <footer class="page-footer teal">
            <PromisableButton :click="save" title="Save"/>
        </footer>
    </div>
</template>

<script>
    import {mapActions, mapState} from 'vuex';
    import PromisableButton from '../../components/PromisableButton';
    import ParameterConfigForm from './ParameterConfigForm';
    import ScriptConfigForm from './ScriptConfigForm';
    import ScriptParamList from './ScriptParamList';

    export default {
        name: 'ScriptConfig',
        components: {PromisableButton, ScriptParamList, ParameterConfigForm, ScriptConfigForm},
        props: {
            scriptName: {
                type: String
            }
        },

        methods: {
            ...mapActions('scriptConfig', ['init', 'save'])
        },

        computed: {
            ...mapState('scriptConfig', {
                scriptConfig: 'scriptConfig',
                loadingError: 'error'
            })
        },

        watch: {
            scriptName: {
                immediate: true,
                handler(scriptName) {
                    this.init(scriptName);
                }
            }
        }
    }

</script>

<style scoped>
    .script-config {
        display: flex;
        flex-direction: column;
        height: 100%;
    }

    .script-config h5 {
        margin-left: 0.75rem;
        margin-top: 0.5rem;
        margin-bottom: 2rem;
    }

    .script-config .script-config-content {
        padding-top: 1.5em;
        flex: 1 1 0;
        min-height: 0;
        overflow-y: auto;
    }

    .script-config .script-config-content .container {
        height: 100%;
    }

    footer.page-footer {
        padding-top: 0;

        flex: 0 0 0;
        display: flex;
        justify-content: center;
    }

    .script-config >>> footer.page-footer a.btn-flat {
        height: 48px;
        line-height: 48px;
        width: 128px;
        color: white;
        text-align: center;
        font-size: 16px;
    }

    .script-config >>> footer.page-footer .preloader-wrapper {
        width: 30px;
        height: 30px;
    }

    .script-config >>> footer.page-footer .spinner-layer {
        border: white;
    }

    .script-config >>> footer.page-footer .btn-flat i {
        font-size: 24px;
    }
</style>
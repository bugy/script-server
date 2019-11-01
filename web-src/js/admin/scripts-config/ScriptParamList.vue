<template>
    <ul class="collapsible popout" ref="parametersPanel">
        <ParamListItem :key="paramKeys.get(param)" :param="param" @delete="deleteParam(param)"
                       @moveDown="moveDown(param)"
                       @moveUp="moveUp(param)"
                       v-for="param in parameters"/>
        <li @click.stop="addParam" class="add-param-item">
            <div class="collapsible-header">
                <i class="material-icons">add</i>Add
            </div>
        </li>
    </ul>
</template>

<script>
    import {hasClass, guid} from '../../common'
    import ParamListItem from './ParamListItem';

    export default {
        name: 'ScriptParamList',

        components: {ParamListItem},

        props: {
            parameters: {
                type: Array,
                default: () => []
            }
        },

        data() {
            return {
                openingNewParam: false,
                paramKeys: new Map()
            }
        },

        mounted: function () {
            M.Collapsible.init(this.$refs.parametersPanel, {
                onOpenEnd: () => {
                    this.openingNewParam = false;
                }
            });
        },

        methods: {
            deleteParam(param) {
                const index = this.parameters.indexOf(param);
                if (index < 0) {
                    return;
                }

                let activeElementIndex = this.getActiveParamIndex();

                const collapsible = M.Collapsible.getInstance(this.$refs.parametersPanel);
                if (index === activeElementIndex) {
                    collapsible.close(activeElementIndex);
                } else if (activeElementIndex > index) {
                    collapsible.open(activeElementIndex - 1);
                }

                this.$delete(this.parameters, index);

                const toast = M.toast({
                    html: '<span>Deleted ' + param.name + '</span>' +
                        '<button class="btn-flat toast-action">' +
                        'Undo' +
                        '</button>',
                    displayLength: 8000
                });

                $(toast.el).find('button').click(() => {
                    toast.dismiss();
                    const insertPosition = Math.min(index, this.parameters.length);
                    this.parameters.splice(insertPosition, 0, param);
                });
            },

            moveUp(param) {
                const index = this.parameters.indexOf(param);
                if (index <= 0) {
                    return;
                }

                const prevParam = this.parameters[index - 1];
                this.$set(this.parameters, index - 1, param);
                this.$set(this.parameters, index, prevParam);

                const collapsible = M.Collapsible.getInstance(this.$refs.parametersPanel);
                const activeParamIndex = this.getActiveParamIndex();
                if (activeParamIndex === index) {
                    collapsible.open(index - 1);
                } else if (activeParamIndex === (index - 1)) {
                    collapsible.open(index);
                }
            },

            moveDown(param) {
                const index = this.parameters.indexOf(param);
                if ((index < 0) || (index > this.parameters.length - 2)) {
                    return;
                }

                const nextParam = this.parameters[index + 1];
                this.$set(this.parameters, index + 1, param);
                this.$set(this.parameters, index, nextParam);

                const collapsible = M.Collapsible.getInstance(this.$refs.parametersPanel);
                const activeParamIndex = this.getActiveParamIndex();
                if (activeParamIndex === index) {
                    collapsible.open(index + 1);
                } else if (activeParamIndex === (index + 1)) {
                    collapsible.open(index);
                }
            },

            addParam() {
                const lastIndex = this.parameters.length;

                const newParameter = {
                    name: undefined,
                    param: undefined,
                    description: undefined,
                    default: undefined,
                    constant: undefined,
                    min: undefined,
                    max: undefined,
                    no_value: undefined,
                    values: undefined,
                    file_extensions: undefined,
                    type: undefined,
                    required: undefined,
                    secure: undefined,
                    multiple_arguments: undefined,
                    separator: undefined,
                    file_recursive: undefined,
                    file_type: undefined
                };
                this.parameters.splice(lastIndex, 0, newParameter);

                this.setParameterKey(newParameter);

                this.$nextTick(() => {
                    this.openingNewParam = true;

                    const collapsible = M.Collapsible.getInstance(this.$refs.parametersPanel);
                    collapsible.open(lastIndex);
                });
            },

            getActiveParamIndex() {
                let activeElementIndex = -1;
                for (let i = 0; i < this.$refs.parametersPanel.childNodes.length; i++) {
                    const child = this.$refs.parametersPanel.childNodes[i];

                    if (hasClass(child, 'active')) {
                        activeElementIndex = i;
                        break;
                    }
                }
                return activeElementIndex;
            },

            scrollToNewParam() {
                const parameterElements = $(this.$refs.parametersPanel).children('li');
                const newParamElement = parameterElements[parameterElements.length - 2];

                newParamElement.scrollIntoView();
            },

            setParameterKey(parameter) {
                if (this.paramKeys.has(parameter)) {
                    return;
                }
                this.paramKeys.set(parameter, guid(32));
            }
        },

        watch: {
            openingNewParam(openingNewParam) {
                if (!openingNewParam) {
                    return;
                }

                let interval = null;
                interval = setInterval(() => {
                    try {
                        this.scrollToNewParam();
                    } finally {
                        if (!this.openingNewParam) {
                            clearInterval(interval);
                        }
                    }
                }, 40);
            },

            parameters :{
                immediate: true,
                handler(parameters) {
                    for (const parameter of parameters) {
                        this.setParameterKey(parameter);
                    }
                }
            }
        }
    }
</script>

<style scoped>

</style>
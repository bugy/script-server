<template>
    <li class="param-list-item">
        <div class="collapsible-header teal lighten-5 param-header">
            <i :class="{'red-text': errorText}" :title="errorText" class="material-icons">
                {{ errorText ? 'warning' : 'unfold_more' }}
            </i>
            <span :class="{'red-text': errorText}">{{ param.name }}</span>
            <div style="flex: 1 1 0"></div>
            <a @click.stop="$emit('delete')" class="btn-flat waves-circle">
                <i class="material-icons">delete</i>
            </a>
            <a @click.stop="$emit('moveUp')" class="btn-flat waves-circle">
                <i class="material-icons">arrow_upward</i>
            </a>
            <a @click.stop="$emit('moveDown')" class="btn-flat waves-circle">
                <i class="material-icons">arrow_downward</i>
            </a>
        </div>
        <div class="collapsible-body">
            <ParameterConfigForm :value="param" @error="handleError($event)"/>
        </div>
    </li>
</template>

<script>
    import {forEachKeyValue, isEmptyObject, isEmptyString, isNull} from '../../common';
    import ParameterConfigForm from './ParameterConfigForm';

    export default {
        name: 'ParamListItem',
        components: {ParameterConfigForm},

        props: {
            param: {
                type: Object
            }
        },

        data() {
            return {
                errors: null
            }
        },

        computed: {
            errorText() {
                const errors = this.errors;
                if (isEmptyObject(errors)) {
                    return null;
                }

                let text = '';
                forEachKeyValue(errors, (key, value) => text += key + ': ' + value + '\n');
                return text;
            }
        },

        methods: {
            handleError(error) {
                if (isNull(this.errors)) {
                    this.errors = {};
                }

                const fieldName = error['fieldName'];
                if (isEmptyString(error.message)) {
                    this.$delete(this.errors, fieldName);
                } else {
                    this.$set(this.errors, fieldName, error.message);
                }
            }
        }
    }
</script>

<style scoped>
    .collapsible-header.param-header {
        padding-top: 8px;
        padding-bottom: 8px;
        align-items: center;
    }

    .btn-flat {
        padding: 0;
    }

    .btn-flat i {
        margin-right: 0;
    }

</style>
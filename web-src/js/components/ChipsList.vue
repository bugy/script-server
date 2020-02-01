<template>
    <div class="chips-list">
        <label>{{ title }}</label>
        <div class="chips" ref="chips"></div>
    </div>
</template>

<script>
    import * as M from 'materialize-css';
    import {isNull} from '../common';

    export default {
        name: 'ChipsList',
        props: {
            value: {
                type: Array,
                default: () => []
            },
            title: {
                type: String,
                default: ''
            }
        },

        mounted: function () {
            this.initChips([]);
        },

        watch: {
            value: {
                immediate: true,
                handler(newValue) {
                    if (!isNull(this.$refs.chips)) {
                        this.updateChips();
                    } else {
                        this.$nextTick(() => {
                            this.updateChips();
                        });
                    }
                }
            }
        },

        methods: {
            initChips(data) {
                M.Chips.init(this.$refs.chips, {
                    data,
                    onChipAdd: this.updateValue,
                    onChipDelete: this.updateValue
                });
            },

            updateValue() {
                const instance = M.Chips.getInstance(this.$refs.chips);
                this.$emit('input', instance.chipsData.map(d => d.tag));
            },

            updateChips() {
                this.initChips(this.value.map(v => ({tag: v})));
            }
        }
    }
</script>

<style scoped>
    .chips-list {
        padding-left: 0.75em;
        padding-right: 0.75em;
        position: relative;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    .chips-list .chips.input-field {
        min-height: 3rem;
        margin-top: 0;
        margin-bottom: 8px;
    }

    .chips-list label {
        position: absolute;
        top: -13px;
    }

    .chips-list >>> .chip {
        margin-bottom: 3px;
    }

</style>
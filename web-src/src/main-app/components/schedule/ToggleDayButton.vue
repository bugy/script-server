<template>
    <div :class="{active: value}"
         @click="$emit('input', !value)"
         class="toggle-day-button"
         v-trim-text>
        {{text}}
    </div>
</template>

<script>
    export default {
        name: 'RoundToggleButton',
        props: {
            text: {
                type: String,
                default: '?'
            },
            value: {
                type: Boolean,
                default: false
            }
        }
    }
</script>

<style scoped>
    .toggle-day-button {
        height: 28px;
        width: 28px;
        line-height: 28px;

        text-align: center;

        border-radius: 14px;
        background-color: rgba(0, 0, 0, 0.05);

        cursor: pointer;
        text-transform: uppercase;

        font-size: 11px;
        color: rgba(0, 0, 0, 0.6);
    }

    .toggle-day-button.active {
        color: white;
        background-color: #26a69a;
    }
</style>
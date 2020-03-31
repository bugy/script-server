<template>
    <div class="readonly-field">
        <label>{{ title }}</label>
        <label>{{ value || "&nbsp;" }}</label>
    </div>
</template>

<script>
    export default {
        name: 'readonly-field',
        props: ['title', 'value']
    }
</script>

<style scoped>
    .readonly-field {
        color: rgba(0, 0, 0, 0.87);
    }

    .readonly-field label:nth-child(1) {
        display: block;
        font-size: 0.8rem;
    }

    .readonly-field label:nth-child(2) {
        display: block;
        font-size: 1rem;
        color: inherit;
    }
</style>
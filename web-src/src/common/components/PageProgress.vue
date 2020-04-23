<template>
    <div class="page-progress">
        <div class="progress-wrapper">
            <div class="progress">
                <div class="indeterminate"></div>
            </div>
        </div>
    </div>
</template>

<script>
    export default {
        name: 'PageProgress'
    }
</script>

<style scoped>
    .page-progress {
        margin-top: 3em;
    }

    .progress-wrapper {
        max-width: 500px;
        margin-left: auto;
        margin-right: auto;
    }
</style>
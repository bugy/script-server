<template>
    <div class="promisable-button">
        <a @click="onClick" class="save-button waves-effect waves-teal btn-flat">
            <i :title="error" class="material-icons" v-if="error">warning</i>
            <div class="preloader-wrapper small active" v-if="inProgress">
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
            {{ title }}
        </a>
    </div>
</template>

<script>
    import {isEmptyString} from '../common';

    export default {
        name: 'PromisableButton',
        props: {
            title: {
                type: String,
                default: 'Save'
            },
            click: Function
        },

        data() {
            return {
                inProgress: false,
                error: null
            }
        },

        methods: {
            onClick() {
                this.error = null;
                this.inProgress = true;

                this.click().then(() => {
                    this.error = null;
                    this.inProgress = false;
                })
                    .catch((e) => {
                        if (!isEmptyString(e.userMessage)) {
                            this.error = e.userMessage;
                        } else {
                            this.error = 'Failed to ' + this.title;
                        }
                        this.inProgress = false;
                    })
            }
        }
    }
</script>

<style scoped>
    .promisable-button > a {
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .preloader-wrapper,
    i {
        margin-right: 1rem;
    }
</style>
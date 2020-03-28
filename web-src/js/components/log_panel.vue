<template>
    <div class="log-panel">
        <div class="log-panel-shadow"
             v-bind:class="{
             'shadow-top': !atTop && atBottom,
             'shadow-bottom': atTop && !atBottom,
             'shadow-top-bottom': !atTop && !atBottom}">
        </div>
        <a class="copy-text-button btn-flat waves-effect btn-floating" @click="copyLogToClipboard">
            <i class="material-icons">content_copy</i>
        </a>
    </div>
</template>

<script>
    import {copyToClipboard, isNull} from '../common';
    import {TerminalModel} from './terminal/terminal_model';
    import {Terminal} from './terminal/terminal_view';

    export default {
        props: {
            'autoscrollEnabled': {
                type: Boolean,
                default: true
            }
        },
        data: function () {
            return {
                atBottom: false,
                atTop: false,
                mouseDown: false,
                scrollUpdater: null,
                needScrollUpdate: false
            }
        },

        created() {
            this.terminalModel = new TerminalModel();
            this.terminal = new Terminal(this.terminalModel);
        },

        mounted: function () {
            const terminal = this.terminal.element;
            terminal.classList.add('log-content');
            terminal.addEventListener('scroll', () => this.recalculateScrollPosition());
            terminal.addEventListener('mousedown', () => this.mouseDown = true);
            terminal.addEventListener('mouseup', () => this.mouseDown = false);

            this.$el.insertBefore(terminal, this.$el.children[0]);

            this.recalculateScrollPosition();
            window.addEventListener('resize', this.revalidateScroll);

            this.scrollUpdater = window.setInterval(() => {
                if (!this.needScrollUpdate) {
                    return;
                }
                this.needScrollUpdate = false;

                let autoscrolled = false;
                if (this.autoscrollEnabled) {
                    autoscrolled = this.autoscroll();
                }

                if (!autoscrolled) {
                    this.recalculateScrollPosition();
                }
            }, 40);
        },

        methods: {
            recalculateScrollPosition: function () {
                var logContent = this.terminal.element;

                var scrollTop = logContent.scrollTop;
                var newAtBottom = (scrollTop + logContent.clientHeight + 5) > (logContent.scrollHeight);
                var newAtTop = scrollTop === 0;

                // sometimes we can get scroll update (from incoming text) between autoscroll and this method
                if (!this.needScrollUpdate) {
                    this.atBottom = newAtBottom;
                    this.atTop = newAtTop;
                }
            },

            autoscroll: function () {
                var logContent = this.terminal.element;
                if ((this.atBottom) && (!this.mouseDown)) {
                    logContent.scrollTop = logContent.scrollHeight;
                    return true;
                }
                return false;
            },

            revalidateScroll: function () {
                this.needScrollUpdate = true;
            },

            setLog: function (text) {
                this.terminalModel.clear();

                this.appendLog(text);
            },

            appendLog: function (text) {
                if (isNull(text) || (text === '')) {
                    return;
                }

                this.terminalModel.write(text);

                this.revalidateScroll();
            },

            removeInlineImage: function (output_path) {
                this.terminalModel.removeInlineImage(output_path);
            },

            setInlineImage: function (output_path, download_url) {
                this.terminalModel.setInlineImage(output_path, download_url);
            },

            copyLogToClipboard: function () {
                copyToClipboard(this.terminal.element);
            }
        },

        beforeDestroy: function () {
            window.removeEventListener('resize', this.revalidateScroll);
            window.clearInterval(this.scrollUpdater);
        }
    }

</script>

<style scoped>
    .log-panel {
        flex: 1;

        position: relative;
        min-height: 0;

        background: #f4f2f0;

        width: 100%;

        border: solid 1px rgba(51, 51, 51, 0.12);
        border-radius: 2px;
    }

    .log-panel-shadow {
        position: absolute;

        width: 100%;
        min-height: 100%;
        top: 0;
        z-index: 5;

        pointer-events: none;
    }

    .shadow-top-bottom {
        box-shadow: 0 7px 8px -4px #888888 inset, 0 -7px 8px -4px #888888 inset;
        -webkit-box-shadow: 0 7px 8px -4px #888888 inset, 0 -7px 8px -4px #888888 inset;
        -moz-box-shadow: 0 7px 8px -4px #888888 inset, 0 -7px 8px -4px #888888 inset;
    }

    .shadow-top {
        box-shadow: 0 7px 8px -4px #888888 inset;
        -webkit-box-shadow: 0 7px 8px -4px #888888 inset;
        -moz-box-shadow: 0 7px 8px -4px #888888 inset;
    }

    .shadow-bottom {
        box-shadow: 0 -7px 8px -4px #888888 inset;
        -webkit-box-shadow: 0 -7px 8px -4px #888888 inset;
        -moz-box-shadow: 0 -7px 8px -4px #888888 inset;
    }

    .log-panel >>> .log-content img {
        max-width: 100%
    }

    .log-panel .copy-text-button {
        position: absolute;
        right: 12px;
        bottom: 8px;
    }

    .log-panel .copy-text-button i {
        color: #00000030;
    }

</style>

'use strict';

(function () {

    //noinspection JSAnnotator
    Vue.component('readonly-field', {
        template: `
            <div class="readonly-field">
                    <label>{{ title }}</label>
                    <label>{{ value }}</label>                
            </div>`,
        props: ['title', 'value']
    });

    // It's partial implementation of log panel from main script execution
    // In the next version, this implementation should be improved and used on the main screen
    // (after testing vue js on admin panel for at least 1 release)
    //   Not yet supported: log appending (at the moment it's replaced on any 'log' field amend)
    //noinspection JSAnnotator
    Vue.component('log-panel', {
        template: `
            <div class="log-panel">
                <code class="log-content" 
                    v-on:scroll="recalculateScrollPosition" 
                    ref="logContent"
                    v-on:mousedown="mouseDown = true"
                    v-on:mouseup="mouseDown = false">{{ log }}</code>
                <div class="log-panel-shadow" v-bind:class="{
                        'shadow-top': !atTop && atBottom,
                        'shadow-bottom': atTop && !atBottom,
                        'shadow-top-bottom': !atTop && !atBottom
                    }">
                    
                </div>
            </div>`,

        props: {
            'log': String,
            'autoscrollEnabled': {
                type: Boolean,
                default: true
            }
        },
        data: function () {
            return {atBottom: false, atTop: false, mouseDown: false}
        },
        watch: {
            log: function () {
                this.$nextTick(this.revalidateScroll);
            }
        },
        mounted: function () {
            this.recalculateScrollPosition();
            window.addEventListener('resize', this.revalidateScroll);
        },
        methods: {
            recalculateScrollPosition: function () {
                var logContent = this.$refs.logContent;

                this.atBottom = (logContent.scrollTop + logContent.clientHeight + 5) > (logContent.scrollHeight);
                this.atTop = logContent.scrollTop === 0;
            },

            autoscroll: function () {
                var logContent = this.$refs.logContent;
                if ((this.atBottom) && (!this.mouseDown)) {
                    logContent.scrollTop = logContent.scrollHeight;
                }
            },

            revalidateScroll: function () {
                if (this.autoscrollEnabled) {
                    this.autoscroll();
                }
                this.recalculateScrollPosition();
            }
        },
        beforeDestroy: function () {
            window.removeEventListener('resize', this.revalidateScroll)
        }
    });
}());
import Vue from 'vue';

(function () {

    //noinspection JSAnnotator
    Vue.component('readonly-field', {
        template: `
            <div class="readonly-field">
                    <label>{{ title }}</label>
                    <label>{{ value || "&nbsp;" }}</label>                
            </div>`,
        props: ['title', 'value']
    });

}());
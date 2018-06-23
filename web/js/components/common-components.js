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

}());
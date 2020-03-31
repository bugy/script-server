<template>
    <div class="input-field combobox-search" @keydown="filteredStopPropagation">
        <input :id="id"
               :value="value"
               @input="inputFieldChanged"
               @blur="focused = false"
               @focus="focused = true"
               ref="textField"/>

        <label :for="id" v-bind:class="{ active: labelActive }">Search</label>
    </div>
</template>

<script>
    import {addClass, destroyChildren, hasClass, isEmptyString, isNull, removeClass, uuidv4} from '../../common';

    export default {
        name: 'ComboboxSearch',

        props: {
            comboboxWrapper: {
                type: Object
            }
        },

        data() {
            return {
                id: null,
                value: '',
                focused: false,
                heightStyle: null
            }
        },
        mounted() {
            this.id = 'combobox-search-' + uuidv4();

            if (this.$el.parentNode) {
                this.$el.parentNode.removeChild(this.$el);
            }
        },

        computed: {
            labelActive() {
                return !isEmptyString(this.value) || this.focused;
            }
        },

        watch: {
            comboboxWrapper: function () {
                const searchElement = this.$el;
                const comboboxWrapper = this.comboboxWrapper;

                if (searchElement.parentNode) {
                    searchElement.parentNode.removeChild(searchElement);
                }

                if (!comboboxWrapper.dropdown) {
                    return;
                }

                disableDropdownCloseOnInput(comboboxWrapper);

                appendCallback(comboboxWrapper.dropdown.options, 'onOpenEnd', () => {
                    this.focus();

                    if (isNull(this.heightStyle)) {
                        this.heightStyle = comboboxWrapper.dropdown.dropdownEl.style.height;
                    }

                    comboboxWrapper.dropdown.dropdownEl.style.maxHeight = this.heightStyle;
                    comboboxWrapper.dropdown.dropdownEl.style.height = null;
                });

                appendCallback(comboboxWrapper.dropdown.options, 'onCloseEnd', () => {
                    comboboxWrapper.dropdown.dropdownEl.style.maxHeight = null;
                });

                $(comboboxWrapper.dropdown.dropdownEl).find('.disabled').each(function () {
                    destroyChildren(this);

                    this.appendChild(searchElement);

                    addClass(this, 'combobox-search-header');
                });

                this.executeSearch(this.value);

                this.heightStyle = null;
            }
        },

        methods: {
            inputFieldChanged() {
                const textField = this.$refs.textField;
                const value = textField.value;

                this.value = value;

                this.executeSearch(value);
            },

            focus() {
                this.$refs.textField.focus();
            },

            executeSearch(searchString) {
                searchString = searchString.toLowerCase();

                $(this.comboboxWrapper.dropdown.dropdownEl).children('li').each(function () {
                    const keepElement = this.textContent.toLowerCase().includes(searchString)
                        || hasClass(this, 'disabled')
                        || hasClass(this, 'selected');

                    if (keepElement) {
                        removeClass(this, 'search-hidden');
                    } else {
                        addClass(this, 'search-hidden');
                    }
                });
            },

            // when user inputs a letter, combobox focuses an element starting with this letter
            // and nothing is written to search field in this case
            // so we hide any non-control keys from the combobox
            filteredStopPropagation(e) {
                if ((e.which === M.keys.ESC)
                    || (e.which === M.keys.ENTER)
                    || (e.which === M.keys.ARROW_DOWN)
                    || (e.which === M.keys.ARROW_UP)
                    || (e.which === M.keys.TAB)) {
                    return;
                }

                e.stopPropagation();
            }
        }
    }

    function disableDropdownCloseOnInput(comboboxWrapper) {
        if (!comboboxWrapper.dropdown.options.closeOnClick) {
            return;
        }

        comboboxWrapper.dropdown.options.closeOnClick = false;

        const autoclose = (e) => {
            const closest = $(e.target).closest('.input-field');
            if (closest.hasClass('combobox-search')) {
                return;
            }

            setTimeout(() => {
                comboboxWrapper.dropdown.close();
            }, 0);
            comboboxWrapper.dropdown.isTouchMoving = false;
        };
        comboboxWrapper.dropdownOptions.addEventListener('click', autoclose, {capture: true});
    }

    function appendCallback(object, callbackField, newCallback) {
        if (object[callbackField]) {
            const oldCallback = object[callbackField];
            object[callbackField] = () => {
                oldCallback();
                newCallback();
            };

        } else {
            object[callbackField] = newCallback;
        }
    }

</script>

<style scoped>
    .input-field.combobox-search {
        margin-top: 0;
        margin-bottom: 0;
        padding: 1.5rem 1rem 0.5rem;
    }

    .main-app-content .input-field.combobox-search > label {
        left: 16px;
        top: 0.5rem;
    }

    .main-app-content .input-field.combobox-search > label.active {
        transform: translateY(-20%) scale(0.8);
    }
</style>
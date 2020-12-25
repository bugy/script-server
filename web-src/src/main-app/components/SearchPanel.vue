<template>
    <div class="search-panel-root">
        <div :class="{collapsed:!showSearchField}" class="search-panel">
            <input :disabled="!showSearchField" @blur="focusLostHandler" autocomplete="off" class="search-field"
                   name="searchField"
                   placeholder="Search script"
                   ref="searchField"
                   type="search"
                   v-bind:value="value"
                   v-on:input="$emit('input', $event.target.value)">
        </div>
        <input :alt="showSearchField ? 'Clear search' : 'Search script'" :src="searchImage"
               @click="clickHandler"
               @mousedown="mouseDownHandler"
               class="search-button"
               type="image">
    </div>
</template>

<script>
import ClearIcon from '@/assets/clear.png'
import SearchIcon from '@/assets/search.png'
import {setInputValue} from '@/common/utils/common';

export default {
  name: 'SearchPanel',
  data() {
    return {
      showSearchField: false,
      openSearchOnTheNextClick: true
    }
  },
  props: {
    value: {
      type: String,
      default: ''
    }
  },
  methods: {
    clickHandler() {
      if (this.openSearchOnTheNextClick) {
        this.showSearchField = true;

        this.$nextTick(() => {
          this.$refs.searchField.focus();
                    });

                } else {
                    this.showSearchField = false;
                    setInputValue(this.$refs.searchField, '', true);
                }
                this.openSearchOnTheNextClick = true;
            },

            mouseDownHandler() {
                this.openSearchOnTheNextClick = !this.showSearchField;
            },

            focusLostHandler() {
                if (this.value === '') {
                    this.showSearchField = false;
                }
            }
        },
        computed: {
            searchImage() {
                return this.showSearchField ? ClearIcon : SearchIcon;
            }
        }
    }
</script>

<style scoped>
    .search-panel-root {
        display: flex;
        align-items: center;
    }

    .search-field[type=search] {
        width: 100%;
        height: 1.5rem;
        font-size: 1rem;
        float: right;
        padding: 0;
        margin: 0;
    }

    .search-panel {
      padding: 16px 10px;
      width: calc(100% - 80px - 10px);
      vertical-align: middle;
      position: absolute;
      top: 0;
      right: 80px;
      background: var(--background-color);
      transition: width 0.3s;
    }

    .search-panel.collapsed {
        width: 0;
    }

    .search-button {
        margin-top: 1px;
    }

</style>
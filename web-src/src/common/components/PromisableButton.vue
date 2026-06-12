<template>
  <v-btn
      :disabled="!enabled"
      :loading="inProgress"
      class="save-button promisable-button"
      color="primary"
      variant="text"
      @click="onClick">

    <v-icon v-if="iconText && !error" class="button-icon">{{ iconText }}</v-icon>
    <v-icon v-if="error" :title="error" class="button-icon">warning</v-icon>
    {{ title }}
  </v-btn>
</template>

<script>
// Vuetify migration: v-btn with the built-in :loading spinner replaces the
// materialize flat button + embedded preloader markup. The promise handling
// (click -> inProgress -> error with userMessage) is untouched. The
// preloaderStyle prop is accepted for compatibility but unused: the v-btn
// spinner sizes itself to the button.
import {isEmptyString} from '@/common/utils/common';

export default {
  name: 'PromisableButton',
  props: {
    title: {
      type: String,
      default: 'Save'
    },
    click: Function,
    preloaderStyle: {
      type: Object,
      default: () => {
      }
    },

    enabled: {
      default: true
    },

    iconText: {
      type: String,
      default: null
    }
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
.button-icon {
  margin-right: 1rem;
}
</style>

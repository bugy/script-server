<template>
  <p class="script-loading-text">
    Loading {{ loadingDots }}
  </p>
</template>

<script>
import {randomInt} from '@/common/utils/common';

export default {
  name: 'ScriptLoadingText',

  data() {
    return {
      loadingDots: '',
      loaderTimer: null,
      counter: 0
    }
  },

  props: {
    loading: {
      type: Boolean,
      default: false
    },
    script: {
      type: String,
      default: null
    },
    delay: {
      type: Number,
      default: 1000
    }
  },

  methods: {
    updateLoadingIndicator() {
      if (!this.loading) {
        this.loadingDots = '';
        return;
      }

      if (this.loaderTimer) {
        clearInterval(this.loaderTimer);
      }

      this.loadingDots = '..';
      this.counter = 0;
      this.loaderTimer = setInterval(() => {
        this.counter++;

        if (this.counter > 30) {
          return;
        }

        if (this.counter === 30) {
          this.loadingDots += ' loading time is unknown';
          return;
        }

        if ((this.counter === 6) || (this.counter === 13) || (this.counter === 21)) {
          let attempts = 0;
          while (attempts++ < 10) {
            const phrase = phrases[randomInt(0, phrases.length)];
            if (this.loadingDots.includes(phrase)) {
              continue;
            }

            this.loadingDots += ' ' + phrase + ' ..';
            return;
          }
        }

        this.loadingDots += '.'
      }, this.delay)
    }
  },

  watch: {
    script: {
      immediate: true,
      handler() {
        this.updateLoadingIndicator();
      }
    },

    loading: {
      immediate: true,
      handler() {
        this.updateLoadingIndicator();
      }
    }
  },

  destroyed: function () {
    if (this.loaderTimer) {
      clearInterval(this.loaderTimer);
      this.loaderTimer = null;
    }
  }
}

const phrases = [
  'wait a bit more',
  'doing my best',
  'don\'t leave me',
  'thanks for waiting',
  'Zzzzz',
  '42',
  'I\'m still alive',
  'what a lovely weather today',
  'some bits got stuck',
  'patience is power',
  'almost done'];
</script>

<style scoped>
.script-loading-text {
  color: var(--font-color-medium);
}

</style>

<template>
  <a :disabled="!enabled" class="save-button waves-effect btn-flat promisable-button"
     @click="onClick">

    <i v-if="error" :title="error" class="material-icons">warning</i>
    <div v-if="inProgress" :style="preloaderStyle" class="preloader-wrapper small active">
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
</template>

<script>
import '@/common/materializecss/imports/spinner'
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
a.promisable-button {
  display: flex;
  align-items: center;
  justify-content: center;
}

.preloader-wrapper,
i {
  margin-right: 1rem;
}
</style>
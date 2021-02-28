<template>
  <div class="log-panel">
    <div class="log-panel-shadow"
         v-bind:class="{
             'shadow-top': !atTop && atBottom,
             'shadow-bottom': atTop && !atBottom,
             'shadow-top-bottom': !atTop && !atBottom}">
    </div>
    <a class="copy-text-button btn-icon-flat waves-effect waves-circle" @click="copyLogToClipboard">
      <i class="material-icons">content_copy</i>
    </a>
  </div>
</template>

<script>
import {copyToClipboard, isNull} from '@/common/utils/common';
import {TerminalOutput} from '@/common/components/terminal/ansi/TerminalOutput'
import {TextOutput} from '@/common/components/terminal/text/TextOutput'
import {HtmlIFrameOutput} from '@/common/components/terminal/html/HtmlIFrameOutput'
import {HtmlOutput} from '@/common/components/terminal/html/HtmlOutput'

export default {
  props: {
    'autoscrollEnabled': {
      type: Boolean,
      default: true
    },
    'outputFormat': {
      type: String,
      default: 'terminal'
    }
  },
  data: function () {
    return {
      atBottom: false,
      atTop: false,
      mouseDown: false,
      scrollUpdater: null,
      needScrollUpdate: false,
      text: ''
    }
  },

  mounted: function () {
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

    this.renderOutputElement()
  },

  methods: {
    recalculateScrollPosition: function () {
      var logContent = this.output.element;

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
      var logContent = this.output.element;

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
      this.text = ''
      this.output.clear()

      this.recalculateScrollPosition()

      this.appendLog(text)
    },

    appendLog: function (text) {
      if (isNull(text) || (text === '')) {
        return;
      }

      this.text += text
      this.output.write(text);

      this.revalidateScroll();
    },

    removeInlineImage: function (output_path) {
      this.output.removeInlineImage(output_path);
    },

    setInlineImage: function (output_path, download_url) {
      this.output.setInlineImage(output_path, download_url);
    },

    copyLogToClipboard: function () {
      copyToClipboard(this.output.element);
    },

    renderOutputElement: function () {
      if (!this.output || !this.$el) {
        return
      }

      const oldOutputs = this.$el.getElementsByClassName('log-content')
      Array.from(oldOutputs).forEach(old => this.$el.removeChild(old))

      const terminal = this.output.element;
      terminal.classList.add('log-content');
      terminal.addEventListener('scroll', () => this.recalculateScrollPosition());
      terminal.addEventListener('mousedown', () => this.mouseDown = true);
      terminal.addEventListener('mouseup', () => this.mouseDown = false);

      this.$el.insertBefore(terminal, this.$el.children[0]);

      this.revalidateScroll()
    }
  },

  beforeDestroy: function () {
    window.removeEventListener('resize', this.revalidateScroll);
    window.clearInterval(this.scrollUpdater);
  },

  watch: {
    outputFormat: {
      immediate: true,
      handler: function () {
        switch (this.outputFormat) {
          case 'terminal':
            this.output = new TerminalOutput()
            break
          case 'html_iframe':
            this.output = new HtmlIFrameOutput()
            break
          case 'html':
            this.output = new HtmlOutput()
            break
          case 'text':
            this.output = new TextOutput()
            break
          default:
            console.log('WARNING! Unknown outputFormat: "' + this.outputFormat + '". Falling back to terminal')
            this.output = new TerminalOutput()
        }

        this.output.write(this.text)

        this.renderOutputElement()
      }
    }
  }
}

</script>

<style scoped>
.log-panel {
  flex: 1;

  position: relative;
  min-height: 0;

  background: var(--surface-color);

  width: 100%;

  border: solid 1px var(--separator-color);
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
  box-shadow: 0 7px 8px -4px rgba(0, 0, 0, 0.4) inset, 0 -7px 8px -4px rgba(0, 0, 0, 0.4) inset;
}

.shadow-top {
  box-shadow: 0 7px 8px -4px rgba(0, 0, 0, 0.4) inset;
}

.shadow-bottom {
  box-shadow: 0 -7px 8px -4px rgba(0, 0, 0, 0.4) inset;
}

.log-panel >>> .log-content.terminal-output img {
  max-width: 100%
}

.log-panel .copy-text-button {
  position: absolute;
  right: 8px;
  bottom: 4px;
}

.log-panel .copy-text-button i {
  color: var(--font-color-disabled);
}

/*noinspection CssInvalidPropertyValue,CssOverwrittenProperties*/
.log-panel >>> .log-content {
  display: block;
  overflow-y: auto;
  height: 100%;
  width: 100%;

  font-size: .875em;

  padding: 1.5em;

  white-space: pre-wrap; /* CSS 3 */
  white-space: -moz-pre-wrap; /* Mozilla, since 1999 */
  white-space: -o-pre-wrap; /* Opera 7 */
  overflow-wrap: break-word;

  -ms-word-break: break-all;
  /* This is the dangerous one in WebKit, as it breaks things wherever */
  word-break: break-all;
  /* Instead use this non-standard one: */
  word-break: break-word;

  /* Adds a hyphen where the word breaks, if supported (No Blink) */
  -ms-hyphens: auto;
  -moz-hyphens: auto;
  -webkit-hyphens: auto;
  hyphens: auto;
}


</style>

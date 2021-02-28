import {addClass} from '@/common/utils/common'

export class HtmlIFrameOutput {
    constructor() {
        this.element = document.createElement('iframe')
        addClass(this.element, 'html-iframe-output')

        this.element.style.border = 'none'
        this.element.style.fontFamily = 'monospace'
        this.element.style.padding = 0
    }

    clear() {
        this.element.srcdoc = ''
    }

    write(text) {
        this.element.srcdoc += text
    }

    removeInlineImage(outputPath) {

    }

    setInlineImage(outputPath, downloadUrl) {
        console.log('WARNING! inline images are not supported for html output')
    }

}
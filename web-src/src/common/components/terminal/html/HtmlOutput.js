import {addClass} from '@/common/utils/common'

export class HtmlOutput {
    constructor() {
        this.element = document.createElement('code')
        addClass(this.element, 'html-output')
        this.element.style.whiteSpace = 'normal'
    }

    clear() {
        this.element.innerHTML = ''
        this.element.lastTrimmedChildIndex = 0
    }

    write(text) {
        this.element.innerHTML += text
    }

    removeInlineImage(outputPath) {

    }

    setInlineImage(outputPath, downloadUrl) {
        console.log('WARNING! inline images are not supported for html output')
    }
}
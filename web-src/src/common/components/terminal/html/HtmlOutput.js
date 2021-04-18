import {addClass, destroyChildren} from '@/common/utils/common'
import DOMPurify from 'dompurify'

export class HtmlOutput {
    constructor() {
        this.element = document.createElement('code')
        addClass(this.element, 'html-output')
        this.element.style.whiteSpace = 'normal'

        this.rawText = ''
    }

    clear() {
        this.element.innerHTML = ''
        this.element.lastTrimmedChildIndex = 0
        this.rawText = ''
    }

    write(text) {
        this.rawText += text

        destroyChildren(this.element)
        this.element.appendChild(DOMPurify.sanitize(this.rawText, {RETURN_DOM_FRAGMENT: true}))
    }

    removeInlineImage(outputPath) {

    }

    setInlineImage(outputPath, downloadUrl) {
        console.log('WARNING! inline images are not supported for html output')
    }
}
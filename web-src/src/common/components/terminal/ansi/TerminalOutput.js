import {TerminalModel} from '@/common/components/terminal/ansi/terminal_model'
import {Terminal} from '@/common/components/terminal/ansi/terminal_view'
import {addClass} from '@/common/utils/common'

export class TerminalOutput {
    constructor() {
        this.terminalModel = new TerminalModel();
        this.terminal = new Terminal(this.terminalModel);

        this.element = this.terminal.element

        addClass(this.element, 'terminal-output')
    }

    clear() {
        this.terminalModel.clear()
    }

    write(text) {
        this.terminalModel.write(text)
    }

    removeInlineImage(output_path) {
        this.terminalModel.removeInlineImage(output_path)
    }

    setInlineImage(output_path, download_url) {
        this.terminalModel.setInlineImage(output_path, download_url)
    }
}
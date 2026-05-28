import {trimTextNodes} from '@/common/utils/common'

// Vue 3 directive hook names:
//   inserted       → beforeMount
//   componentUpdated → updated
export default {
    'trim-text': {
        beforeMount: trimTextNodes,
        updated: trimTextNodes
    }
}

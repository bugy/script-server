import {trimTextNodes} from '@/common/utils/common'

export default {
    'trim-text': {
        inserted: trimTextNodes,
        componentUpdated: trimTextNodes
    }
}
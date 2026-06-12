import {defineStore} from 'pinia'

export const usePageStore = defineStore('page', {
    state: () => ({
        pageLoading: false
    }),
    actions: {
        setLoading(loading) {
            this.pageLoading = loading
        }
    }
})

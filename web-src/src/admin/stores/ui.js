import {defineStore} from 'pinia'

export const useAdminUiStore = defineStore('adminUi', {
    state: () => ({
        subheader: null
    }),
    actions: {
        setSubheader(subheader) {
            this.subheader = subheader || null
        }
    }
})

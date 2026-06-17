import {defineStore} from 'pinia'
import {axiosInstance} from '@/common/utils/axios_utils'

export const useAuthStore = defineStore('auth', {
    state: () => ({
        enabled: false,
        authenticated: true,
        admin: false,
        username: null,
        canEditCode: false
    }),
    actions: {
        init() {
            axiosInstance.get('auth/info').then(({data}) => {
                this.enabled = data.enabled
                this.admin = data.admin
                this.username = data.username
                this.canEditCode = data.canEditCode
            })
        },
        setAuthenticated(authenticated) {
            this.authenticated = authenticated
        },
        logout() {
            return axiosInstance.post('logout')
                .catch(error => {
                    const {status} = error.response
                    if (status !== 405) throw error
                })
        }
    }
})

import { defineStore } from 'pinia'

export const useTokenStore = defineStore('TokenStore', {
    state: () => {
        return {
            access_token: null,
            refresh_token: null,
        }
    },

    actions: {

        async login(context, payload) {
            const response = await axios.post('/auth/token', {
                username: payload.username,
                password: payload.password
            }, {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            }
            )

            context.commit('login', {
                result: response.data,
            })
        },

        async userMe(context) {

            const access_token = store.getters.access_token

            axios.defaults.headers.common = { 'Authorization': "Bearer " + access_token }

            const response = await axios.get("/user/me")
            context.commit('userMe', {
                result: response,
            })
        },

        async updateAccessToken(context, token) {
            context.commit('updateAccessToken', { result: token })
        }
    }

}
)

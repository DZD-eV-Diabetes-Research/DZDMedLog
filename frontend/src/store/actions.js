import axios from "axios"

export default {
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

        console.log(response.data)
        context.commit('login', {
            result: response.data,
        })
    },

}
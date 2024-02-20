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
    async getToken(context, payload){ 
 
        axios.defaults.headers.common = {'Authorization' : "Bearer " + payload}

        const response = await axios.post('/auth/refresh', {
            headers: {
                'Content-Type': 'json'
            }
        })

        console.log(response.data)
        context.commit('refresh', {
            result: response.data,
        })

    }
}
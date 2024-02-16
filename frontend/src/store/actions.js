import axios from "axios"

export default {
    async login(context, payload) {
        const response = await axios.post('http://localhost:8888/auth/token', {
            username: payload.username,
            password: payload.password
        }, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        }
        )

        // if (!response.data) {
        //     const error = new Error("Can't connect please try again later")
        //     throw error
        // }

        console.log(response.data)
        context.commit('login', {
            result: response.data,
        })
    }
}
export default {
    async login(context, payload){
        var formData = new FormData()
        formData.append('username', payload.username)
        formData.append('password', payload.password)


        const response = await fetch('http://localhost:8888/auth/token',{
            method: 'POST', body:formData}
            )

        const responseData = await response.json()

        if (!response.ok){
            const error = new Error(responseData.message)
            throw error
        }

        console.log(responseData)
        context.commit('login',{
            refresh_token: responseData.refresh_token,
            access_token: responseData.access_token,
        })
    }
}
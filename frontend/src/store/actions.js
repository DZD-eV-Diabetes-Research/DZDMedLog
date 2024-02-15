export default {
    async login(context, payload){
        var formData = new FormData()
        formData.append('username', payload.username)
        formData.append('password', payload.password)


        const response = await fetch('http://localhost:8888/auth/token',{
            method: 'POST', body:formData}
            )
            //body: JSON.stringify({
            //    username : payload.username,
            //    password : payload.password,
            //    returnSecureToken : true
            // })
         

        const responseData = await response.json()

        if (!response.ok){
            console.log(responseData)
            const error = new Error(responseData.message)
            throw error
        }

        console.log(responseData)
        context.commit('login',{
            refresh_token: responseData.refresh_token,
            refresh_token_expires_in : responseData.refresh_token_expires_in,
            access_token: responseData.access_token,
            access_token_expires_at : responseData.access_token_expires_at

        })
    }
}
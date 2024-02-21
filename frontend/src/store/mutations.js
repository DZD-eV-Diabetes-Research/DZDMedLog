 export default {
    login(state, payload){
        state.refresh_token = payload.result.refresh_token,
        state.access_token = payload.result.access_token
    },
    refresh(state, payload){
        state.access_token = payload.result.access_token
    },
    userMe(state, payload){
        state.email = payload.result.data.email
        state.display_name = payload.result.data.display_name
        state.roles = payload.result.data.roles
        state.user_name = payload.result.data.user_name

    },
    updateAccessToken(state,payload){
        state.access_token = payload
    }
 }
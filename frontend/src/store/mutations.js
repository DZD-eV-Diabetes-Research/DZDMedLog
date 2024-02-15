 export default {
    login(state, payload){
        state.refresh_token = payload.refresh_token,
        state.access_token = payload.access_token
    }
 }
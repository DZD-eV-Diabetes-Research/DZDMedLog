 export default {
    login(state, payload){
        state.result = payload,
        state.refresh_token = payload.result.refresh_token,
        state.access_token = payload.result.access_token
    }
 }
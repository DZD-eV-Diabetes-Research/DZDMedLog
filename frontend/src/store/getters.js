export default {
    access_token(state){
        return state.access_token.result
    },
    refresh_token(state){
        return state.refresh_token
    },
    email(state){
        return state.email
    },
    display_name(state){
        return state.display_name
    },
    roles(state){
        return state.roles
    },
    user_name(state){
        return state.user_name
    },
}
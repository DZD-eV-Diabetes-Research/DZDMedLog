import { createStore} from 'vuex'
import axios from "axios"

import rootActions from './actions'
import rootGetters from './getters'
import rootMutations from './mutations'

const store = createStore({
    state(){
        return{
            access_token : null,
            refresh_token: null
        }
    },
    actions: rootActions,
    getters: rootGetters,
    mutations: rootMutations,
})

export default store
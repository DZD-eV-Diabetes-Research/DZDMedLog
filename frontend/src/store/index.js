import { createStore} from 'vuex'

import rootActions from './actions'
import rootGetters from './getters'
import rootMutations from './mutations'

const store = createStore({
    state(){
        return{
            access_token : null,
            refresh_token: null,
            my_api: import.meta.env.VITE_API
        }
    },
    actions: rootActions,
    getters: rootGetters,
    mutations: rootMutations,
})

export default store
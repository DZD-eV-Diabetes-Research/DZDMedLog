import { createStore} from 'vuex'

import rootActions from './actions'
import rootGetters from './getters'
import rootMutations from './mutations'

const store = createStore({
    state(){
        return{
            test: "Hallo"
        }
    },
    actions: rootActions,
    getters: rootGetters,
    mutations: rootMutations,
})

export default store
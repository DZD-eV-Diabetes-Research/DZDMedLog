import { defineStore } from 'pinia'

interface TokenState {
    access_token: string
    refresh_token: string
    loggedIn: boolean
    my_401: boolean
    
}

export const useTokenStore = defineStore('TokenStore',{
    id: "token-store",
    state: (): TokenState => ({
    
        access_token: "",
        refresh_token: "",
        loggedIn: false,
        my_401: false

    }),
    actions: {
        async login(username, password, event: FormSubmitEvent<Schema>) {
            const userStore = useUserStore();
            const body = new FormData()
            body.append("username", username) 
            body.append("password", password)
          
            try{
              const data = await $fetch("http://localhost:8888/auth/token", {
                method: "POST",
                body,
              }) 
            
                this.my_401 = false
                this.access_token = data.access_token
                this.refresh_token = data.refresh_token
                this.loggedIn = true

                userStore.userMe()

                const router = useRouter()
                router.push({ path: "/user" })
              
            }
              catch (err) {
                this.my_401 = true
              }
    }
},
    persist: true
}) 
import { defineStore } from 'pinia'

interface TokenState {
  access_token: string
  refresh_token: string
  loggedIn: boolean
  my_401: boolean
  expiredToken:boolean
  oidcTokenURL: string

}

export const useTokenStore = defineStore('TokenStore', {
  id: "token-store",
  state: (): TokenState => ({

    access_token: "",
    refresh_token: "",
    loggedIn: false,
    my_401: false,
    oidcTokenURL: "",
    expiredToken: false,

  }),
  actions: {

    async login(username, password, event: FormSubmitEvent<Schema>) {
      const { $api } = useNuxtApp();
      const userStore = useUserStore();
      const body = new FormData()
      body.append("username", username)
      body.append("password", password)

      const runtimeConfig = useRuntimeConfig()
      try {
        const data = await $api(runtimeConfig.public.baseURL + "auth/token", {
          method: "POST",
          body,
        })

        this.my_401 = false
        this.access_token = data.access_token
        this.refresh_token = data.refresh_token
        this.loggedIn = true
        this.expiredToken = false

        userStore.userMe()

        const router = useRouter()
        router.push({ path: "/user" })

      }
      catch (err) {
        console.log(err);

        this.my_401 = true
      }
    },
    async loginViaOpenIDToken(token) {
      const userStore = useUserStore();
      this.my_401 = false
      this.access_token = token.value.access_token
      this.refresh_token = token.value.refresh_token
      this.loggedIn = true
      this.oidcTokenURL = ""
      this.expiredToken = false
      userStore.userMe()

      const router = useRouter()
      router.push({ path: "/" })

    },
    set401(value: boolean) {
      this.my_401 = value;
    },
    setOidcTokenURL(value: string){
      this.oidcTokenURL = value
    },
  },
  persist: {
    storage: localStorage,
  }
}) 
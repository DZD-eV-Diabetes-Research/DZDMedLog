export default defineNuxtRouteMiddleware(async (to, from) => {

    const tokenStore = useTokenStore()

    if (to.path === '/login/oidc') {
      console.log("tokenstore loggedstatus: "+ tokenStore.loggedIn); 
    }

    if (to.path === '/my_test') {
      console.log("my_test"); 
    }

    else if (to.path !== '/' && !tokenStore.loggedIn) {
      return navigateTo('/')
    } 

    else if (to.path === '/' && tokenStore.loggedIn) {
      return navigateTo('/user')
    }
  })
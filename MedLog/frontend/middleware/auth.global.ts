export default defineNuxtRouteMiddleware((to, from) => {

    const tokenStore = useTokenStore()

    if (to.path !== '/' && !tokenStore.loggedIn) {
      return navigateTo('/')
    } 

    if (to.path == '/' && tokenStore.loggedIn) {
      return navigateTo('/user')
    }   
  })
export default defineNuxtRouteMiddleware(async (to, from) => {

    const tokenStore = useTokenStore()

    // If you are not loggedIn you are only allowed to visit the /login/oidc page to enable login via openIDConnect
    if (to.path === '/login/oidc') {
      console.log("tokenstore loggedstatus: "+ tokenStore.loggedIn); 
    }

    // Otherwise if you are not logged in you will be directed to the landing/login page to log in
    else if (to.path !== '/' && !tokenStore.loggedIn) {
      return navigateTo('/')
    } 

    // If you are logged in and try to access the landing/login page you will be directed to the /user page
    else if (to.path === '/' && tokenStore.loggedIn) {
      return navigateTo('/user')
    }   
  })
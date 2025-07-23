export default defineNuxtRouteMiddleware(async (to, from) => {
  const userStore = useUserStore()

  if (to.path !== '/'){
    try {
      await userStore.userMe()
    } catch (error) {
      console.log(error);
      // no need to redirect, logic is handled by api
    }
  }
})

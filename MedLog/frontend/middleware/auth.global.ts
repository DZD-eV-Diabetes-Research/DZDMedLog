export default defineNuxtRouteMiddleware(async (to) => {
  const userStore = useUserStore()

  if (to.path !== '/login'){
    try {
      await userStore.setUserInfo()
    } catch (error) {
      console.log(error);
      // no need to redirect, logic is handled by plugins/api
    }
  }
})

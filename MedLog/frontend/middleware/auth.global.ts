export default defineNuxtRouteMiddleware(async (to) => {
  const roleStore = useRoleStore();
  const userStore = useUserStore();

  console.log('path', to.path)

  if (to.path !== '/login'){
    try {
      await roleStore.loadRoles()
      await userStore.setUserInfo()
    } catch (error) {
      console.log(error);
      // no need to redirect, logic is handled by plugins/api
    }
  }
})

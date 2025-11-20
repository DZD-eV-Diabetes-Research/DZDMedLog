<template>
  <div>
    <UIBaseCard>
      <div v-if="healthStatus?.healthy" class="flex flex-col justify-center">
        <div v-if="loginMethods" class="flex flex-col space-y-2">
          <UAlert
              v-if="loginError"
              color="orange"
              variant="subtle"
              title="Login-Fehler"
              :description="loginError"
          />
          <div v-for="loginMethod in loginMethods" :key="loginMethod.auth_type">
            <LoginForm
              v-if="loginMethod.auth_type === 'basic'"
              @login="({username, password}) => login(loginMethod.login_endpoint, username, password)"
            />
            <div v-else>
              <UButton :class="[getRandomColorClass(), 'rounded-lg']" @click="loginOIDC(loginMethod)">
                Login via: {{ loginMethod.display_name }}
              </UButton>
            </div>
          </div>
        </div>
        <div class="mt-4">
          <p>
            Kein Account?
            <a
              href="https://auth.dzd-ev.org/" target="_blank"
              class="hover:border-[#ec372d] hover:border-b-2">Registrieren Sie sich hier.</a>
          </p>
        </div>
      </div>
      <div v-else class="flex flex-col space-y-8 text-center">
        <h3 class="text-4xl text-red-500">Der Backendstatus ist "not healthy"</h3>
        <p class="text-lg text-red-500">Bitte wenden Sie sich an ihren Admin</p>
        <p class="text-lg text-red-500">{{ healthError }}
        </p>
      </div>
    </UIBaseCard>
  </div>
</template>



<script setup lang="ts">
import { useMedlogapi } from '#imports';

const toast = useToast();
const userStore = useUserStore();
const route = useRoute()

const { data: healthStatus, error: healthError } = await useMedlogapi("/api/health")

const { data: loginMethods } = await useMedlogapi("/api/auth/list")

const loginError = ref('');

const login = async (endpoint: string, username: string, password: string) => {
  loginError.value = ""
  const { error } = await useMedlogapi(endpoint, {
    method: "POST",
    body: {
      "username": username,
      "password": password
    },
  });

  if (error) {
    loginError.value = error.value.toString() ?? "Benutzername oder Passwort falsch"
    return
  }

  await userStore.setUserInfo()

  await navigateTo('/')
}

const loginOIDC = async function (oidc_method) {
  try {

    console.log('target path is', route.query.target_path)
    if (route.query.target_path === undefined) {
      window.location.href = `${oidc_method.login_endpoint}?target_path=/`
      // navigateTo(`${oidc_method.login_endpoint}?target_path=/`, { external: true })
    } else {
      window.location.href = `${oidc_method.login_endpoint}?target_path=${route.query.target_path}`
    }

  } catch (error) {
    toast.add({
      title: "Fehler beim Speichern",
      description: error.data?.detail ?? error.message ?? error,
    });
  }
}

// Auto-login check
if (loginMethods && loginMethods.value.length > 0) {
  const autoLoginMethod = loginMethods.value.find(method => method.auto_login)
  if (autoLoginMethod) {    
    loginOIDC(autoLoginMethod)
  }
}

const colors = ["border border-fuchsia-400 bg-fuchsia-100 hover:bg-fuchsia-300 hover:border-white text-fuchsia-400 hover:text-white", "border bg-purple-100 border-purple-400 hover:bg-purple-300 hover:border-white text-purple-400 hover:text-white", "border bg-indigo-100 border-indigo-400 hover:bg-indigo-300 hover:border-white text-indigo-400 hover:text-white", "border bg-violet-100 border-violet-400 hover:bg-violet-300 hover:border-white text-violet-400 hover:text-white",
];
function getRandomColorClass() {
  const color = colors[Math.floor(Math.random() * colors.length)];
  return color;
}
</script>

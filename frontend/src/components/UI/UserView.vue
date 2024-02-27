<template>
    <base-card>
        <h1>Hi {{ userStore.get_user_name }} this is what you should see now</h1>
        <p>This should print your email: {{ userStore.get_email }}</p>
        <p>This should print your display_name: {{ userStore.get_display_name }}</p>
        <p>This should print your roles: {{ userStore.get_roles }}</p>
        <button @click="logout">logout</button>
    </base-card>
</template>

<script>

import { useTokenStore } from '@/stores/TokenStore'
import { useUserStore } from '@/stores/UserStore'

export default {

    setup() {
        const tokenStore = useTokenStore()
        const userStore = useUserStore()
        return { tokenStore, userStore }
    },
    methods: {
        logout() {
            this.userStore.$reset()
            this.tokenStore.$reset()
            this.$router.push("/")
        },
        userMe() {
            try {
                this.userStore.userMe()
            } catch (err) {
                console.log(err)
                this.tokenStore.error = err.response
            }
        }
    }
}

</script>
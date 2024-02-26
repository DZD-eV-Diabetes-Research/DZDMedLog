<template>
    <base-card>
        <form @submit.prevent="submitForm">
            <div class="form__group">
                <label for="user-name">User Name</label>
                <input id="user-name" name="user-name" type="text" v-model.trim="userName">
                <label for="password">Password</label>
                <input id="password" name="password" type="password" v-model.trim="password">
            </div>
            <div>
                <h1 style="color: red" v-if="tokenStore.get_error">{{ tokenStore.get_error }}</h1>
                <button>Login</button>
                <p>No account? <a href="https://auth.dzd-ev.org/" target="_blank">Sign Up</a></p>
            </div>
        </form>
        <button @click="new_token">New Token</button>
        <button @click="logout">Logout</button>
        <button @click="test">userMe</button>
        {{ userStore.get_email }}
        {{ userStore.get_user_name }}

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

    data() {
        return {
            userName: "",
            password: "",
            formIsValid: true,
        }
    },
    methods: {
        test() {
            try {
                this.userStore.userMe()
            } catch (err) {
                console.log(err)
                this.tokenStore.error = err.response
            }
        },

        async new_token() {

            this.tokenStore.error = null
            const payload = {
                username: this.userName,
                password: this.password
            }
            this.tokenStore.login(payload)

        },

        async logout() {
            this.userName = ""
            this.password = ""
            this.userStore.$reset()
            this.tokenStore.$reset()
        },

        async submitForm() {
            this.tokenStore.error = ""
            if (this.userName === '' || this.password.length === 0) {
                this.tokenStore.error = "Please enter a valid username and password"
                this.formIsValid = false
            }
            const payload = {
                username: this.userName,
                password: this.password
            }

            try {
                await this.tokenStore.login(payload)

                try {
                    await this.tokenStore.userMe()
                }
                catch (err) {
                    this.tokenStore.error = err.response
                }
                this.$router.push("/user")

            } catch (err) {
                this.tokenStore.error = "Wrong username or password"
            }
        },
    }
}


</script>

<style lang="scss">
input[type="text"],
input[type=password] {
    border: 2px solid black;
    border-radius: 4px;
}
</style>
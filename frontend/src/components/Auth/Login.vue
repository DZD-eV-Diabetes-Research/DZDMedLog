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
                <p v-if="!formIsValid">Please enter a valid usernam and password</p>
                <h1 style="color: red" v-if="error">{{ error }}</h1>
                <button @click="submitForm()">Login</button>
                <p>No account? <a href="https://auth.dzd-ev.org/" target="_blank">Sign Up</a></p>
                <br>
            </div>
        </form>
    </base-card>
</template>

<script>
export default {
    data() {
        return {
            userName: "",
            password: "",
            formIsValid: true,
            error: "",
        }
    },
    methods: {
        async submitForm() {
            this.error = ""
            if (this.userName === '' || this.password.length === 0) {
                this.formIsValid = false
            }

            const payload = {
                username: this.userName,
                password: this.password
            }

            try {
                await this.$store.dispatch('login', payload)
                this.$router.push("/user")

            } catch (err) {
                this.error = err.message || 'Failed to authenticate, try later.';
            }
        }
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
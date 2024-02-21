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
                <button>Login</button>
                <p>No account? <a href="https://auth.dzd-ev.org/" target="_blank">Sign Up</a></p>
            </div>
        </form>
        <button @click="newToken">New Token</button>
        <button @click="userMe">About myself</button>
        <h1> {{ $store.state.result }} </h1>
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

        async userMe(){
            const payload = this.$store.getters.access_token
            try{
            await this.$store.dispatch("userMe", payload)
            }
            catch(err){
                this.error = err.response
            }
        },

        async newToken() {
            if (!this.$store.getters.refresh_token) {
                this.error = "Please login first"
            }
            else {
                const payload = this.$store.getters.refresh_token
                console.log(payload)
                try {
                    await this.$store.dispatch('getToken', payload)
                } catch (err) {
                    this.error = err.response
                }
            }
        },

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
                //this.$router.push("/user")

            } catch (err) {
                if (err.response.status === 401) {
                    this.error = "Error: 401 " + err.response.data.detail || 'Failed to authenticate, try later.';
                } else if (err.response.status === 422) {
                    this.error = "Error: 422" + " Both fields must contain data" || 'Failed to authenticate, try later.';
                } else {
                    this.error = 'Failed to authenticate, try later.'
                }
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
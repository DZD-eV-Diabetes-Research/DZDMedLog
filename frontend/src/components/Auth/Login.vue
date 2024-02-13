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
                <button @click="submitForm()">Login</button>
                <p>No account? <a href="https://auth.dzd-ev.org/">Sign Up</a></p>
            </div>
        </form>
    </base-card>
</template>

<script>
export default {
    data() {
        return {
            userName: "",
            password: ""
        }
    },
    methods: {
        submitForm() {
            this.userName = "Now we should do stuff here"
            this.password = ""
        }
    }
}
</script>

<style lang="scss">

input[type="text"], input[type=password]{
    border: 2px solid black;
    border-radius: 4px;
}

</style>
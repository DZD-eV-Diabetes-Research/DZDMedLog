<template>
    <form @submit.prevent="submitForm">
        <div class="form__group">
            <label for="user-name">User Name</label>
            <input id="user-name" name="user-name" type="text" v-model.trim="userName">
            <label for="password">Password</label>
            <input id="password" name="password" type="password" v-model.trim="password">
        </div>
        <div>
            <button @click="submitForm()">Login</button>
        </div>
    </form>
    {{ userName }}
    {{ password }}
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
            this.userName = "HALLO"
            //console.log = this.password
        }
    }
}
</script>

<style lang="scss"></style>
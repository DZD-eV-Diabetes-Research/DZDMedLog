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
                <h1 style="color: red" v-if="tokenStore.error">{{ tokenStore.error }}</h1>
                <button>Login</button>
                <p>No account? <a href="https://auth.dzd-ev.org/" target="_blank">Sign Up</a></p>
            </div>
        </form>
    </base-card>
</template>

<script setup lang="ts">

import { ref } from 'vue';
import router from '@/router.ts';

import { useTokenStore } from '@/stores/TokenStore';
import { useUserStore } from '@/stores/UserStore';

const tokenStore = useTokenStore();
const userStore = useUserStore();

const userName = ref<string>("");
const password = ref<string>("");
const formIsValid = ref<boolean>(true);

async function submitForm(): Promise<void> {
    tokenStore.error = "";

    if (!userName.value || password.value.length === 0) {
        tokenStore.error = "Please enter a valid username and password";
        formIsValid.value = false;
    }
    const payload = {
        username: userName.value,
        password: password.value        
    };
    
    try {
        await tokenStore.login(payload);

        try {
            await userStore.userMe();
        } catch (err: any) {            
            tokenStore.error = err.response;
        }

        router.push("/user")

    } catch (err) {      
        tokenStore.error = "Wrong username or password";
    }
}
</script>

<style lang="scss">
input[type="text"],
input[type="password"] {
    border: 2px solid black;
    border-radius: 4px;
}
</style>

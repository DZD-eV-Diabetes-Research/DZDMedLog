<template>
    <base-card>
        <h4 v-if="tokenStore.error" style="color: red">{{ tokenStore.error }}</h4>
        <Vueform :endpoint="false" @submit="submitLogin">
            <TextElement name="user-name" input-type="text" label="User Name" rules="required" />
            <TextElement name="password" input-type="password" label="Password" rules="required" />
            <ButtonElement name="login" button-label="Login" :submits="true" align="center" />
        </Vueform>
        <p>No account? <a href="https://auth.dzd-ev.org/" target="_blank">Sign Up</a></p>
    </base-card>

</template>

<script setup lang="ts">

import router from '@/router.ts';

import { useTokenStore } from '@/stores/TokenStore';
//import { useUserStore } from '@/stores/UserStore';
import BaseCard from '@/components/UI/BaseCard.vue';

const tokenStore = useTokenStore();
//const userStore = useUserStore();


async function submitLogin(response: any): Promise<void> {

    tokenStore.error = ""

    const payload = {
        username: response.data['user-name'],
        password: response.data['password']
    };
    try {
        await tokenStore.login(payload);
        console.log(payload);
    } catch (error: any) {
        console.log("HEY");
        console.log(error);
    }
    //userStore.userMe()
    router.push("/user")
}

</script>

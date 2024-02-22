<template>
    <base-card>
        <h1>Hi {{ $store.getters.user_name }} this is what you should see now</h1>
        <h3>access {{ $store.getters.access_token }}</h3>
        <p>This should print your email: {{ $store.getters.email }}</p>
        <p>This should print your display_name: {{ $store.getters.display_name }}</p>
        <p>This should print your roles: {{ $store.getters.roles }}</p>
        <button @click="logout">logout</button>
    </base-card>
</template>

<script>

export default {
    methods: {
        logout(){
            console.log("test")
        }
    }
}


</script>
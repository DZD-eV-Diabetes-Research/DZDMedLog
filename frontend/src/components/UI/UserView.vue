<template>
    <base-card>
        <h1>Hi {{ $store.getters.user_name }} this is what you should see now</h1>
        <p>This should print your email: {{ $store.getters.email }}</p>
        <p>This should print your display_name: {{ $store.getters.display_name }}</p>
        <p>This should print your roles: {{ $store.getters.roles }}</p>
    </base-card>
</template>

<script>

</script>
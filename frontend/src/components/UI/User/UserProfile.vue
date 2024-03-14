<template>
  <base-card style="text-align: center;">
    <h3>User name: {{ userStore.user_name }}</h3>
    <h5>Email: {{ userStore.email }}</h5>
    <h5>Display name: {{ userStore.display_name }}</h5>
    <h5>Roles:</h5>
    <p v-for="role in userStore.roles">{{ role }}</p>
  </base-card>
  <div class="naked">
    <button class="edit">Edit</button>
  </div>
</template>

<script>
import { useUserStore } from '@/stores/UserStore'
import { RouterLink } from 'vue-router';

export default {
  setup() {
    const userStore = useUserStore()
    return { userStore }
  },
}
</script>

<style scoped>
.naked {
    display: flex;
    justify-content: space-between; 
    align-items: center;
    margin: 1rem 30rem;
    border-radius: 12px;
}

.edit {
    background-color: #50e469;
    color: #fff;
    border: none;
    border-radius: 5px;
    margin: auto;
}

.edit:hover {
    background-color: #29a329;
    color: #fff
}


</style>
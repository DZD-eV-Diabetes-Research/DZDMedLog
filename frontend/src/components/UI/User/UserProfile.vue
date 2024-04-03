<template>
  <base-card style="text-align: center;">
    <h3>User name: {{ userStore.userName }}</h3>
    <h5>Email: {{ userStore.email }}</h5>
    <h5>Display name: {{ userStore.displayName }}</h5>
    <h5>Roles:</h5>
    <p v-for="role in userStore.roles">{{ role }}</p>
  </base-card>
  <div class="naked">
    <button @click="editModal=true" class="edit">Edit</button>
  </div>
  <modal-vue title="User bearbeiten" :show="editModal" @close="editModal = false">
        <template #body>
          <form @submit.prevent="submitForm">
                <div class="form__group">
                    <label for="display_name">Display Name</label>
                    <input id="display_name" name="Display Name" type="text" v-model.trim="studyName" class="input-field">
                    <label for="user_mail">Email</label>
                    <input id="user_mail" name="user_mail" type="email" v-model.trim="displayName" class="input-field">
                    <p v-if="!formIsValid" style="color: red;">Die Felder dürfen nicht leer sein</p>
                </div>
                <!-- <div>
                    <button @click="submitStudy">Anlegen</button>
                </div> -->
            </form>
        </template>
    </modal-vue>
</template>

<script setup lang="ts">
import { useUserStore } from '@/stores/UserStore'
import { ref } from 'vue';

const userStore = useUserStore()

const editModal = ref<boolean>(false);
const formIsValid = ref<boolean>(true);
const studyName = ref<string>("")
const displayName = ref<string>("")


function submitForm(){
  console.log("Hey")
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
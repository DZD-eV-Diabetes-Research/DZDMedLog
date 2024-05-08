<template>
  <base-card style="text-align: center;">
    <h3>User name: {{ userStore.userName }}</h3>
    <h5>Email: {{ userStore.email }}</h5>
    <h5>Display name: {{ userStore.displayName }}</h5>
    <h5>Roles:</h5>
    <p v-for="role in userStore.roles">{{ role }}</p>
  </base-card>
  <div class="naked">
    <button @click="editModal = true" class="edit">Edit</button>
  </div>
  <modal-vue title="User bearbeiten" :show="editModal" @close="editModal = false" :titleColor="'#42b983'">
        <template #body>
          <form @submit.prevent="submitForm">
                <div class="form__group">
                    <label for="display_name">Display Name</label>
                    <input id="display_name" name="Display Name" type="text" v-model.trim="studyName" class="input-field">
                    <label for="user_mail">Email</label>
                    <input id="user_mail" name="user_mail" type="email" v-model.trim="displayName" class="input-field">
                    <p v-if="!formIsValid" style="color: red;">Die Felder dürfen nicht leer sein</p>
                </div>
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
const email = ref<string>("")
const displayName = ref<string>("")


async function submitForm() {
  const payload = {
    "email": email.value,
    "display_name": displayName.value
  }
  try {
    await userStore.updateUser(payload);
    await userStore.userMe();
  } catch (error: any) {
    console.log(error.message);
  }

  editModal.value = false
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
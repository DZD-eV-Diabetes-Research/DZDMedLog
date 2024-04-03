<template>
    <base-card v-if="!studyStore.studies">
        <h2 v-if="userStore.isAdmin">Aktuell sind keine Studien aufgelistet bitte, legen Sie eine Studie an</h2>
        <h2 v-if="!userStore.isAdmin">Aktuell sind keine Studien aufgelistet bitte, wenden Sie sich an einen Admin</h2>
    </base-card>
    <base-card v-on:click="selectStudy(study)" v-for="study in studyStore.studies.items" :key="study.id"
        style="text-align: center">
        <h3>{{ study.display_name }}</h3>
    </base-card>
    <div v-if="userStore.isAdmin" class="button-container">
        <button @click="showModal = true">Studie anlegen</button>
    </div>
    <modal-vue @close="resetModal" title="Studie anlegen" :show="showModal" :title-color="'#42b983'">
        <template #header>
        </template>
        <template #body>
            <form @submit.prevent="submitForm">
                <div class="form__group">
                    <label for="study-name">Studienname</label>
                    <input id="study-name" name="study-name" type="text" v-model.trim="studyName">
                    <label for="display-name">Abkürzung</label>
                    <input id="display-name" name="display-name" type="text" v-model.trim="displayName">
                    <p v-if="!formIsValid" style="color: red;">Die Felder dürfen nicht leer sein</p>
                </div>
                <div>
                    <button @click="submitStudy">Anlegen</button>
                </div>
            </form>
        </template>
    </modal-vue>
</template>

<script setup lang="ts">

import { ref } from 'vue';
import router from '@/router.ts';

import { useTokenStore } from '@/stores/TokenStore'
import { useUserStore } from '@/stores/UserStore'
import { useStudyStore } from '@/stores/StudyStore'

const tokenStore = useTokenStore()
const userStore = useUserStore()
const studyStore = useStudyStore()

const showModal = ref<boolean>(false)
const formIsValid = ref<boolean>(true)
const studyName = ref<string>("")
const displayName = ref<string>("")

function resetModal(): void {
    showModal.value = false;
    formIsValid.value = true;
    studyName.value = "";
    displayName.value = "";
}

async function submitStudy() {
    if (studyName.length === 0 || displayName.length === 0) {
        this.formIsValid = false
    } else {
        const payload = {
            display_name: displayName,
            name: studyName
        }
        studyStore.createStudy(payload)
        studyStore.listStudies()
        resetModal()
    }
}

async function selectStudy(study) {
    router.push("/studies/" + study.name)
}


</script>

<style lang="scss" scoped>
.base-card:hover {
    background-color: #ededed;
    cursor: pointer;
}

.button-container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100%;
}

.button-container button {
    background-color: #2eb82e;
    color: #fff;
    border: none;
    border-radius: 5px;
}

.button-container button:hover {
    background-color: #29a329;
}
</style>
<template>
    <base-card v-if="!studyStore.studies || studyStore.studies.length === 0">
        <h2 v-if="userStore.is_admin">Aktuell sind keine Studien aufgelistet bitte, legen Sie eine Studie an</h2>
        <h2 v-if="!userStore.is_admin">Aktuell sind keine Studien aufgelistet bitte, wenden Sie sich an einen Admin</h2>
    </base-card>
    <div v-if="userStore.is_admin" class="button-container">
        <button @click="this.showModal = true">Studie anlegen</button>
    </div>
    <modal-vue title="Studie anlegen" :show="showModal" @close="showModal = false">
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

<script>

import { useTokenStore } from '@/stores/TokenStore'
import { useUserStore } from '@/stores/UserStore'
import { useStudyStore } from '@/stores/StudyStore'

export default {

    setup() {
        const tokenStore = useTokenStore()
        const userStore = useUserStore()
        const studyStore = useStudyStore()
        return { tokenStore, userStore, studyStore }
    },

    data() {
        return {
            showModal: false,
            formIsValid: true,
            studyName: "",
            displayName: ""
        }
    },
    methods: {
        async submitStudy() {
            if (this.studyName.length === 0 || this.displayName.length === 0) {
                this.formIsValid = false
            } else {
                const payload = {
                    display_name: this.displayName, 
                    name: this.studyName
                }
                this.studyStore.createStudy(payload)
                this.studyStore.myStudies()
                this.showModal = false
            }
        }
    }
}


</script>

<style lang="scss" scoped>
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
}

.button-container button:hover {
    background-color: #29a329;
}
</style>
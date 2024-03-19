<template>
    <base-card v-if="!studyStore.studies">
        <h2 v-if="userStore.is_admin">Aktuell sind keine Studien aufgelistet bitte, legen Sie eine Studie an</h2>
        <h2 v-if="!userStore.is_admin">Aktuell sind keine Studien aufgelistet bitte, wenden Sie sich an einen Admin</h2>
    </base-card>
    <base-card v-on:click="selectStudy(study)" v-for="study in studyStore.studies.items" :key="study.id" style="text-align: center">
        <h3>{{ study.display_name }}</h3>
    </base-card>
    <div v-if="userStore.is_admin" class="button-container">
        <button @click="this.showModal = true">Studie anlegen</button>
    </div>
    <modal-vue @close="resetModal" title="Studie anlegen" :show="showModal">
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
        resetModal(){
            this.showModal = false,
            this.formIsValid = true,
            this.studyName = "",
            this.displayName = ""
        },
        async submitStudy() {
            if (this.studyName.length === 0 || this.displayName.length === 0) {
                this.formIsValid = false
            } else {
                const payload = {
                    display_name: this.displayName,
                    name: this.studyName
                }
                this.studyStore.createStudy(payload)
                this.studyStore.listStudies()
                this.showModal = false
                this.formIsValid = true
                this.studyName = ""
                this.displayName = ""
            }
        },
        async selectStudy(study) {
            this.$router.push("/studies/" + study.name)
        }
    }
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
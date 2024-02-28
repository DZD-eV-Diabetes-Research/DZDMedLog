<template>
    <base-card>
        <h3>Hello {{ userStore.get_user_name }}</h3>
        <div class="button-container">
            <button @click="conductInterview">Interview durchführen</button>
            <button @click="searchMedicaments">Medikament suchen</button>
            <h1 v-if="tokenStore.error">{{tokenStore.error}}</h1>
        </div>
    </base-card>
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
    methods: {
        userMe() {
            try {
                this.userStore.userMe()
            } catch (err) {
                console.log(err)
                this.tokenStore.error = err.response
            }
        },
        conductInterview() {
            try {
                this.studyStore.myStudies()
                this.$router.push("/studies")
            } catch (err) {
                console.log(err)
                this.tokenStore.error = err.response
            }
        },
        searchMedicaments() {
            this.$router.push("/construction")
        }
    }
}

</script>

<style scoped>
.button-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.button-container button {
    margin-bottom: 35px;
    /* Adjust the value as needed */
}
</style>
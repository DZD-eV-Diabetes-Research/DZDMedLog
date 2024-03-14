<template>
    <base-card v-if="!study" style="text-align: center;">
        <h1>Oops you shouldn't be here</h1>
        <RouterLink to="/studies">Back to the start</RouterLink>
    </base-card>
    <base-card v-else style="text-align: center;">
        <p>{{ study }}</p>
    </base-card>
    <div v-if="study" class="naked">
        <button @click="deleteModal=true" class="mybutton delete">Delete</button>
        <button @click="editModal=true" class="mybutton edit">Edit</button>
    </div>
    <modal-vue class="delete_modal" title="Studie löschen" :show="deleteModal" @close="deleteModal = false">
        <template #header>
        </template>
        <template #body>
            <h1>not yet implemented</h1>
        </template>
    </modal-vue>
    <modal-vue class="edit_modal" title="Studie bearbeiten" :show="editModal" @close="editModal = false">
        <template #header>
        </template>
        <template #body>
            <h1>not yet implemented</h1>
        </template>
    </modal-vue>
</template>

<script>
import { useStudyStore } from '@/stores/StudyStore'
import { RouterLink } from 'vue-router'
import { useUserStore } from '@/stores/UserStore';


export default {

    setup() {
        const studyStore = useStudyStore()
        const userStore = useUserStore()
        return { studyStore, userStore }
    },
    data() {
        return {
            deleteModal: false,
            editModal: false
        }
    },
    computed: {
        study() {
            return this.studyStore.studies.items.find(({ name }) => name === this.$route.params.study)
        }
    },
    methods: {
    }
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

.mybutton {
    background-color: #2eb82e;
    color: #fff;
    border: none;
    padding: 0.5rem 1rem;
    margin-right: 1.95rem;
    border-radius: 5px;
}

.delete {
    background-color: #f82727;
    color: #fff;
    border: none;
    border-radius: 5px;
}

.delete:hover {
    background-color: #d22020;
    color: #fff
}

.edit {
    background-color: #50e469;
    color: #fff;
    border: none;
    border-radius: 5px;
}

.edit:hover {
    background-color: #29a329;
    color: #fff
}

.delete_modal h3 {
  margin-top: 0;
  color: #f82727;
}
</style>
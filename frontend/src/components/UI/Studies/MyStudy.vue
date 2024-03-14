<template>
    <base-card v-if="!study" style="text-align: center;">
    <h1>Oops you shouldn't be here</h1>
    <RouterLink to="/studies">Back to the start</RouterLink>
    </base-card>
    <base-card v-else style="text-align: center;">
        <p>{{ study }}</p>
    </base-card>
</template>

<script>
import { useStudyStore } from '@/stores/StudyStore'
import { RouterLink } from 'vue-router'
import { toPathString } from '../../../openapi-client-type/common';

export default {

    setup() {
        const studyStore = useStudyStore()
        return { studyStore }
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
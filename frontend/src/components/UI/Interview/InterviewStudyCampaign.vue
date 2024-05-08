<template>
    <base-card>
        <h1>{{router.currentRoute.value.params}}</h1>
        <p>{{ studyStore.study_id }}</p>
        <p>{{ studyStore.interview_id }}</p>
    </base-card>
</template>

<script setup lang="ts">
import router from '@/router.ts';
import { useStudyStore } from '@/stores/StudyStore';

const studyStore = useStudyStore()


</script>
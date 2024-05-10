<template>
    <Layout>
        <UIBaseCard @click="newInterview(item)" v-for="item in [...events.items].reverse()" style="text-align: center">
            <h3>{{stringDoc(item.name)}}</h3>
        </UIBaseCard>
    </Layout>    
</template>

<script setup lang="ts">

const tokenStore = useTokenStore()
const route = useRoute()
const router = useRouter()


const { data: events } = await useFetch(`http://localhost:8888/study/${route.params.study_id}/event`, {
    method: "GET",
    headers: { 'Authorization': "Bearer " + tokenStore.access_token },
})

function newInterview(item){
    router.push({ path: "/interview/" + route.params.study_id + '/event/' +  item.id})
}

const stringDoc = (ugly_name: string): string => {
    let beautiful_name = ugly_name.replaceAll("-"," ")
    const words = beautiful_name.split(" ");
        const capitalizedWords = words.map(word => {
        return word.charAt(0).toUpperCase() + word.slice(1);
    });
        return capitalizedWords.join(" ");
};

</script>

<style scoped>
.base-card:hover {
    background-color: #ededed;
    cursor: pointer;
}
</style>
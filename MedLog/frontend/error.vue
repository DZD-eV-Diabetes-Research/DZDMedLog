<template>
    <NuxtLayout>
        <Layout>
            <UIBaseCard>
                <div class="prose" style="text-align: center;">
                    <template v-if="error === 404">
                        <h1>404!</h1>
                        <p>Sorry, that page doesn't exist.</p>
                    </template>
                    <template v-else>
                        <h1>Dang</h1>
                        <p>
                            <strong>{{ error.message }}</strong>
                        </p>
                        <p>It looks like something broke.</p>
                        <p>Sorry about that.</p>
                    </template>
                    <p>
                        Return to the
                        <NuxtLink to="/login"> startpage.</NuxtLink>
                    </p>
                </div>
            </UIBaseCard>
        </Layout>
    </NuxtLayout>
</template>

<script setup lang="ts">
const error = useError();

</script>

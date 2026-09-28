export default defineNuxtPlugin((nuxtApp) => {
    const toast = useToast();

    nuxtApp.hook('vue:error', (error) => {
        // This is a global fallback for errors not caught and bubbling up within Vue.js
        toast.add({
            title: "Fehler",
            description: useGetErrorMessage(error),
        });
    })
})

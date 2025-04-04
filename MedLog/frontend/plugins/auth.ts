// export default defineNuxtPlugin((nuxtApp) => {
//     console.log("✅ Auth plugin loaded!");

//     const tokenStore = useTokenStore();

//     // Log when the hook is registered
//     nuxtApp.hook('fetch:before', () => {
//         console.log("🔄 fetch:before registered!");
//     });

//     nuxtApp.hook('fetch:response', async (context) => {
//         console.log("✅ fetch:response hook triggered");

//         if (context.response.status === 401) {
//             console.log("❌ Error 401 detected");

//             const responseText = await context.response.text();
//             console.log("🔎 Response Text:", responseText);

//             if (responseText.includes('Signature has expired')) {
//                 console.log("🚨 Token expired! Logging out...");

//                 tokenStore.expiredToken = true;
//                 tokenStore.loggedIn = false;
//                 return navigateTo('/');
//             }
//         }
//     });
// });
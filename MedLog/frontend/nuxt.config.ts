// https://nuxt.com/docs/api/configuration/nuxt-config
import {resolve} from "path"

export default defineNuxtConfig({
  alias:{
    "@": resolve(__dirname, "/")
  },
  devtools: { enabled: true },
  modules: ['@pinia/nuxt', '@pinia-plugin-persistedstate/nuxt', "@nuxt/ui"],
  pinia: {
    storesDirs: ['./stores/**', './custom-folder/stores/**'],
  },
  css: [
    "~/assets/main.scss"
  ],
  postcss: {
    plugins: {
      tailwindcss: {},
      autoprefixer: {},
    },
  },
  colorMode: {
    preference: 'light'
  },
  runtimeConfig: {
    public: {
      baseURL: 'http://localhost:8888/',
    },
  },
  ssr: false,
})
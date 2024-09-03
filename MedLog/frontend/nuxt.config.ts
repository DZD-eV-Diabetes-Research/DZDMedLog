// https://nuxt.com/docs/api/configuration/nuxt-config
import {resolve} from "path"

export default defineNuxtConfig({
  alias:{
    "@": resolve(__dirname, "/")
  },

  devtools: { enabled: true },

  modules: [
    '@pinia/nuxt',
    '@pinia-plugin-persistedstate/nuxt',
    "@nuxt/ui",
    "dayjs-nuxt",
    '@nuxtjs/supabase',
  ],

  pinia: {
    storesDirs: ['./stores/**', './custom-folder/stores/**'],
  },

  dayjs: {
    plugins: ['utc'],
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
      baseURL: '',
    },
  },
  
  supabase: {
    redirectOptions: {
      login: '/',
      callback: '/confirm',
    },
  },

  ssr: false,
  compatibilityDate: '2024-08-29',
})
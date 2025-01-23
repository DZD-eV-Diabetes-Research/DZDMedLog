// https://nuxt.com/docs/api/configuration/nuxt-config
import { resolve } from "path"

export default defineNuxtConfig({
  alias: {
    "@": resolve(__dirname, "/")
  },

  devtools: { enabled: true },

  modules: [
    '@pinia/nuxt',
    '@pinia-plugin-persistedstate/nuxt',
    "@nuxt/ui",
    "dayjs-nuxt",
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
      baseURL: 'http://localhost:8888',
    },
  },

    ssr: false,
    compatibilityDate: '2024-08-29',
  })

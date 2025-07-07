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
    "@nuxt/test-utils/module"
    "nuxt-open-fetch"
  ],

  piniaPersistedstate: {
    cookieOptions: {
      sameSite: 'strict',
    },
  },

  pinia: {
    storesDirs: ['./stores/**', './custom-folder/stores/**'],
  },

  dayjs: {
    plugins: ['utc'],
  },

  css: ["~/assets/main.css"],

  // postcss: {
  //   plugins: {
  //     tailwindcss: {},
  //     autoprefixer: {},
  //   },
  // },

  colorMode: {
    preference: 'light'
  },

  runtimeConfig: {
    public: {
      baseURL: process.env.BASE_URL || '/api/',
      openFetch: {
        checkapi: {
          schema: "../openapi.json",
          baseURL: "/api",
        },
      },
    },
  },
  openFetch: {
    disableNuxtPlugin: true,
    clients: {
      checkapi: {
        schema: "../openapi.json",
        baseURL: "/api",
      },
    },
  },
  nitro: {
    devProxy: {
      "/api": {
        target: "http://localhost:8888/api",
        changeOrigin: true,
        headers: {
          Host: "localhost:3000",
        },
      },
      "/docs": {
        target: "http://localhost:8888/docs",
      },
      "/openapi.json": {
        target: "http://localhost:8888/openapi.json",
      },
    },
  },
    ssr: false,
    compatibilityDate: '2024-08-29',
  })

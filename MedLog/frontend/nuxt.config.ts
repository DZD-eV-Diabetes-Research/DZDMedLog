// https://nuxt.com/docs/api/configuration/nuxt-config
import { resolve } from "path"

export default defineNuxtConfig({
  alias: {
    "@": resolve(__dirname, "/")
  },

  devtools: { enabled: true },

  modules: [
    '@pinia/nuxt',
    "@nuxt/eslint",
    "@nuxt/ui",
    "@nuxt/icon",
    "dayjs-nuxt",
    "@nuxt/test-utils/module",
    "nuxt-open-fetch"
  ],

  pinia: {
    storesDirs: ['./stores/**', './custom-folder/stores/**'],
  },

  dayjs: {
    plugins: ['utc'],
  },

  css: ["~/assets/main.css"],

  colorMode: {
    preference: 'light'
  },

  eslint: {
    // checker: true, // TODO enable this once we settled for a code style
  },
  icon: {
      provider: 'none', // Prevents the dynamic fetching of icons from a CDN
      clientBundle: {
          icons: [
              // Apparently the scan option below does not include icons of stock components.
              // Icons reported as missing can be included here.
              'heroicons:arrows-up-down-20-solid',
              'heroicons:chevron-down-20-solid',
              'heroicons:chevron-left-20-solid',
              'heroicons:chevron-right-20-solid',
              'heroicons:circle-stack-20-solid',
          ],
          scan: true, // Only include used icons in the client bundle to keep the file small
      },
  },

  runtimeConfig: {
    public: {
      baseURL: process.env.BASE_URL || '/api/',
      openFetch: {
        medlogapi: {
          schema: "../openapi.json",
          baseURL: "/api",
        },
      },
    },
  },
  openFetch: {
    disableNuxtPlugin: true,
    clients: {
      medlogapi: {
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

// https://nuxt.com/docs/api/configuration/nuxt-config

export default defineNuxtConfig({
  devtools: { enabled: true },

  modules: [
    '@pinia/nuxt',
    "@nuxt/eslint",
    "@nuxt/ui",
    "@nuxt/icon",
    "dayjs-nuxt",
    "nuxt-open-fetch"
  ],

  pinia: {
    storesDirs: ['./stores/**'],
  },

  dayjs: {
    locales: ['de', 'en'],
    plugins: ['relativeTime', 'utc', 'timezone'],
    defaultLocale: 'de',
    defaultTimezone: 'Europe/Berlin',
  },

  css: ["~/assets/main.css"],

  colorMode: {
    preference: 'light'
  },

  eslint: {
    checker: true,
  },
  icon: {
      provider: 'none', // Prevents the dynamic fetching of icons from a CDN
      clientBundle: {
          icons: [
              // Apparently the scan option below does not include icons of stock components.
              // Icons reported as missing can be included here.
              'heroicons:arrow-path-20-solid',
              'heroicons:arrows-up-down-20-solid',
              'heroicons:bars-arrow-down-20-solid',
              'heroicons:bars-arrow-up-20-solid',
              'heroicons:check-20-solid',
              'heroicons:chevron-down-20-solid',
              'heroicons:chevron-left-20-solid',
              'heroicons:chevron-right-20-solid',
              'heroicons:circle-stack-20-solid',
          ],
          scan: true, // Only include used icons in the client bundle to keep the file small
      },
  },

  typescript: {
    // strict: true,
    // typeCheck: true, TODO enable as soon as all the typing issues are resolved
  },

  runtimeConfig: {
    public: {
      baseURL: process.env.BASE_URL || '/api/',
      openFetch: {
        medlogapi: {
          baseURL: "/api",
        },
      },
    },
  },
  openFetch: {
    clients: {
      medlogapi: {
        schema: "../openapi.json",
        baseURL: "/api",
      },
    },
    openAPITS: {
        rootTypes: true,
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

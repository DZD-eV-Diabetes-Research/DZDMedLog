<template>
  <header class="flex flex-col w-full bg-white py-4 px-10">
    <div class="flex w-full justify-between items-center gap-20">
      <div>
        <NuxtLink to="/" class="text-4xl font-bold text-gray-800 hover:border-[#ec372d] hover:border-b-2">
          DZDMedLog
        </NuxtLink>
      </div>

      <div class="w-60">
        <img src="/img/logos/dzd.png" alt="DZD-Logo" class="max-w-full">
      </div>
    </div>
  </header>

  <div class="mt-8 w-11/12 lg:w-8/12 xl:w-6/12 mx-auto">
    <div v-if="is404">
      <h1 class="text-4xl font-normal text-center mb-4">
        Seite nicht gefunden
      </h1>

      <p class="my-8 text-center text-gray-500 text-xl">
        Der gesuchte Pfad existiert nicht.
      </p>
    </div>

    <div v-else>
      <h1 class="text-4xl font-normal text-center mb-4">
        Kritischer Fehler
      </h1>

      <p class="my-8 text-center text-gray-500 text-xl">
        Es ist ein kritischer Fehler aufgetreten, der die Anwendung grundlegend in ihrer Funktion einschränkt.
      </p>

      <p class="my-8 text-center text-gray-500 text-xl">
        Ursache kann sowohl ein temporäres Problem (z.&#8239;B. Netzwerkverbindung) als auch ein Fehler im Programmcode sein.<br>
        Details entnehmen Sie bitte der nachfolgenden Fehlermeldung.
      </p>

      <p class="my-8 text-center text-gray-500 text-xl">
        Bei unklaren oder anhaltenden Problemen, informieren Sie bitte die Administration.<br>
        <UButton
            v-if="configStore.branding.supportEmail"
            :to="`mailto:${configStore.branding.supportEmail}`"
            variant="link"
            icon="i-heroicons-envelope"
            :external="true"
        >
          {{ configStore.branding.supportEmail }}
        </UButton>
      </p>

      <dl>
        <dt>Fehlermeldung:</dt>
        <dd>{{ error.message }}</dd>

        <dt>Fehlerdetails:</dt>
        <dd><code>{{ error.cause }}</code></dd>

        <dt>Statuscode / -nachricht:</dt>
        <dd>{{ error.statusCode }} / {{ error.statusMessage }}</dd>

        <dt>Version:</dt>
        <dd>{{ configStore.versionInfo.version ?? "N/A" }}</dd>
      </dl>
    </div>

    <div v-if="fetchError" class="mt-8">
      <p class="my-4 text-center text-gray-500 text-xl">
        Beim Laden der Fehlerseite ist ein weiterer Fehler aufgetreten:
      </p>
      <ErrorMessage :error="fetchError" />
    </div>

    <div class="text-center mt-8">
      <UButton
          to="/"
          label="Zur Startseite"
          variant="link"
          icon="i-heroicons-arrow-right-circle"
          class="whitespace-nowrap text-xl"
          trailing
      />
    </div>
  </div>
  <LayoutFooter/>
</template>

<script setup lang="ts">
import type { NuxtError } from '#app';

const configStore = useConfigStore();

const props = defineProps({
  error: {
    type: Object as () => NuxtError,
    required: true,
  },
})

const fetchError = ref();

const is404 = computed(() => {
  return props.error.statusCode === 404
});

onMounted(async () => {
  try {
    await configStore.fetchAllConfigs();
  } catch (error) {
    fetchError.value = error;
  }
});

</script>

<style scoped>
header {
  box-shadow: inset 0 -0.3rem 0 #DA281C
}

dl {
  display: grid;
  grid-template-columns: max-content auto;
}

dt {
  grid-column-start: 1;
  padding: 0.2em 0.4em 0.2em 0.6em;
  font-weight: bold;
}

dt ~ dt, dd ~ dd {
  border-top: 2px solid darkgray;
}

dd {
  grid-column-start: 2;
  padding: 0.2em 0.6em 0.2em 0.4em;
}
</style>

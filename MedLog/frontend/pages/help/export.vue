<script setup lang="ts">
const configStore = useConfigStore();
</script>

<template>
  <section class="container w-11/12 lg:w-8/12 xl:w-6/12 mx-auto mt-8">
    <div class="flex flex-col items-center">
      <h1 class="text-4xl font-normal mb-4">Hilfe zu DZDMedLog</h1>


      <UBreadcrumb
          :links="[{
          label: 'Hilfe',
          icon: 'i-heroicons-question-mark-circle',
          to: '/help'
        }, {
          label: 'Datenexport',
        }]"
          class="self-start"
      />

      <UDivider class="my-2" size="sm" />
      <h2 class="text-3xl font-normal mb-4">Datenexport</h2>
    </div>

    <p>
      Als Admin können Sie die Medikationsdaten einer Studie exportieren.
      Der Zugang erfolgt ebenfalls über die “Studienverwaltung”, ausgehend von der Landingpage.
      Die Landingpage können Sie von überall erreichen, indem Sie auf den Schriftzug <em>{{ configStore.appName }}</em> in der oberen linken Ecke klicken.
      Wählen Sie im Bereich “Studienverwaltung” den “Datenexport” aus.
    </p>
    <p>
      Hier können Sie einen Export generieren und anschließend herunterladen.
    </p>
  </section>
</template>

<style scoped>
p ~ p {
  margin-top: 0.6rem;
}
</style>

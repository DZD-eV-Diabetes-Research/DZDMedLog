<script setup lang="ts">

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
          label: 'Kontoverwaltung ',
        }]"
          class="self-start"
      />

      <UDivider class="my-2" size="sm" />
      <h2 class="text-3xl font-normal mb-4">Kontoverwaltung</h2>
    </div>

    <p>
      Zur Kontoverwaltung und damit zum User-Management gelangen Sie über die entsprechenden Reiter rechts oben auf der DZDMedLog-Seite.
    </p>

    <WarningMessage
      title=""
      message="Bitte beachten Sie, dass nur Benutzer:innen mit User-Management-Rechten Nutzerkonten anlegen oder verwalten können."
      class="mt-4"
    />
  </section>
</template>

<style scoped>
p ~ p {
  margin-top: 0.6rem;
}
</style>

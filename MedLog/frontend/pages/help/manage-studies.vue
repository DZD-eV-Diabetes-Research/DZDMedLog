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
          label: 'Studienverwaltung ',
        }]"
          class="self-start"
      />

      <UDivider class="my-2" size="sm" />
      <h2 class="text-3xl font-normal mb-4">Studienverwaltung</h2>
    </div>

    <p>
      Zur Studienverwaltung – inklusive Anlage der Interviews als Events – gelangen Sie über den Reiter <em>Studienverwaltung</em> rechts oben auf der DZDMedLog-Seite.
    </p>

    <WarningMessage
      title=""
      message="Bitte beachten Sie, dass nur Benutzer:innen mit Admin-Rechten neue Studien und Interviews anlegen können."
      class="mt-4"
    />

    <h3 class="text-xl mt-4 mb-2">Neue Studie anlegen</h3>
    <p>
      Um eine neue Studie anzulegen, klicken Sie auf den Button <em>Studie anlegen</em>.
      Verpflichtend ist hier nur die Angabe eines Namens für die Studie, welcher eindeutig sein muss.
    </p>
    <p>
      Optional können Sie die allgemeinen Einstellungen (v.a. Regeln für die Probanden-ID) und die Struktur (v.a. Events) einer bestehenden Studie übernehmen.
      Daten aus den Interviews werden dabei explizit nicht übernommen.
      Ebenso müssen die individuellen Berechtigungen für die Studie neu vergeben werden.
    </p>
  </section>
</template>

<style scoped>
p ~ p {
  margin-top: 0.6rem;
}
</style>

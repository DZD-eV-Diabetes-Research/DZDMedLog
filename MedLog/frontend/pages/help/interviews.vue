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
          label: 'Interview durchführen',
        }]"
        class="self-start"
      />

      <UDivider class="my-2" size="sm" />
      <h2 class="text-3xl font-normal mb-4">Interview durchführen</h2>
    </div>

    <p>
      Um ein Interview durchzuführen oder zu bearbeiten, klicken Sie auf das "Home"-Icon oder den Schriftzug "Interview durchführen" im linken oberen Bereich der Seite.
      Um ein Interview durchzuführen, muss eine Proband:innen-ID eingegeben werden.
      Falls die Proband:innen-ID noch unbekannt ist, wird der/die Proband:in neu angelegt.
      Falls der/die Proband:in in der Datenbank bereits vorhanden ist, sehen Sie eine Medikationsübersicht des/der Proband:in über die gesamte Studie.
      Jetzt haben Sie die Möglichkeit, ein Interview durchzuführen oder zu bearbeiten.
    </p>
    <p>
      Mit der Auswahl "Interview starten" erscheint die an den/die Proband:in gerichtete Eingangsfrage: "Haben Sie [...] Medikamente [...] eingenommen?".
      Wird diese Frage mit "Nein" beantwortet, wird das Interview ohne Eintragungen für Medikamente angelegt und direkt als abgeschlossen markiert.
      Bei der Auswahl "Ja" gelangen Sie zur Medikationserfassung.
    </p>
    <p>
      Über die Funktion "Medikamente übernehmen" können Sie die Medikamente des letzten abgeschlossenen Interviews für diese:n Proband:in übernehmen.
      Nach Erfassung der Medikation sollte das aktuelle Interview via den Button "Interview abschließen" beendet werden.
    </p>
  </section>
</template>

<style scoped>
p ~ p {
  margin-top: 0.6rem;
}
</style>

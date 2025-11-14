<script setup lang="ts">
import {useMedlogapi} from "#imports";

const { data: config, error: configError, status: configStatus } = await useMedlogapi("/api/config/version")

if (configError.value) {
  console.error('Fehler beim Laden der Konfiguration:', configError.value)
}
</script>

<template>
  <section class="container w-11/12 lg:w-8/12 xl:w-6/12 mx-auto mt-8">
    <h1 class="text-4xl font-normal text-center mb-4">Hilfe zu DZDMedLog</h1>

    <p>DZDMedLog besteht im Kern aus 3 Komponenten:</p>

    <h2 class="text-xl mt-6 mb-2">Teil 1: Studien und Interviews erstellen bzw. verwalten</h2>
    <p>
      Teil 1 finden Sie mittels des Buttons "Studienverwaltung" auf der Landingpage.
      Diese können Sie von überall erreichen, indem Sie auf den DZD-Medlog-Schriftzug in der oberen linken Ecke klicken.
      Bitte beachten Sie, dass nur Benutzer mit Admin-Rechten neue Studien und Interviews anlegen können.
    </p>

    <h2 class="text-xl mt-6 mb-2">Teil 2: Medikamente zu einem Interview hinzufügen</h2>
    <p>
      Teil 2 wird über den Button "Interview durchführen" erreicht.
      Hier wird eine von Ihnen gewählte Probanden-ID verlangt.
      Nun sehen Sie eine Medikationsübersicht des Patienten über die gesamte Studie.
      Hier haben Sie die Möglichkeit, ein Interview durchzuführen oder zu bearbeiten.
    </p>
    <p>
      Sie haben die Möglichkeit, über den Button "Medikationsübernahme" die Medikamente <strong>des letzten abgeschlossenen Events</strong> zu übernehmen.
    </p>

    <h2 class="text-xl mt-6 mb-2">Teil 3: Daten einer Studie exportieren</h2>
    <p>
      Teil 3, den <strong>Datenexport</strong>, erreichen Sie, wie die Verwaltung der Studien, über den Button "Studienverwaltung" von der Landingpage aus.
    </p>
    <p>
      Des weiteren können Sie sich über die Breadcrumbs, am oberen Bildschirmrand, zu den jeweiligen vorher besuchten Seiten klicken
    </p>

    <p>
      Für Admins oder Technikinteressierte finden Sie hier unser <NuxtLink to="https://github.com/DZD-eV-Diabetes-Research/DZDMedLog" :external="true" target="_blank">Repository</NuxtLink>
    </p>

    <div class="flex flex-col text-left space-y-1 mt-4">
      <p class="mb-4">
        Wenn Sie Fragen oder Feedback haben, melden Sie sich gerne:
        <NuxtLink to="mailto:someEmail@someHost.com">someEmail@someHost.com</NuxtLink>
      </p>
      <hr>
      <div v-if="configStatus !== 'error'" class="text-center font-extralight">
        <p>Version: {{ config.version }}</p>
        <p>Branch: {{ config.branch }}</p>
      </div>
      <div v-else>
        {{ configError }}
      </div>
    </div>
  </section>
</template>

<style scoped>
p ~ p {
  margin-top: 0.6rem;
}
</style>

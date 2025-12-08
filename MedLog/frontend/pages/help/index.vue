<script setup lang="ts">
const configStore = useConfigStore();
</script>

<template>
  <section class="container w-11/12 lg:w-8/12 xl:w-6/12 mx-auto mt-8">
    <h1 class="text-4xl font-normal text-center mb-4">Hilfe zu DZDMedLog</h1>

    <UCard class="mb-4">
      <h2 class="text-lg font-semibold mb-2">Inhaltsverzeichnis</h2>
      <ul class="list-inside">
        <li>
          <ULink to="#studien" class="hover:underline">
            Teil 1: Studien und Interviews erstellen bzw. verwalten
          </ULink>
        </li>
        <li>
          <ULink to="#interview" class="hover:underline">
            Teil 2: Medikamente zu einem Interview hinzufügen
          </ULink>
        </li>
        <li class="indent-3">
          <ULink to="#suche">
            Funktionsweise der Medikamentensuche
          </ULink>
        </li>
        <li>
          <ULink to="#export" class="hover:underline">
            Teil 3: Daten einer Studie exportieren
          </ULink>
        </li>
      </ul>
    </UCard>

    <p>DZDMedLog besteht im Kern aus 3 Komponenten:</p>

    <h2 id="studien" class="text-xl mt-6 mb-2">Teil 1: Studien und Interviews erstellen bzw. verwalten</h2>
    <p>
      Teil 1 finden Sie mittels des Buttons "Studienverwaltung" auf der Landingpage.
      Diese können Sie von überall erreichen, indem Sie auf den DZD-Medlog-Schriftzug in der oberen linken Ecke klicken.
      Bitte beachten Sie, dass nur Benutzer mit Admin-Rechten neue Studien und Interviews anlegen können.
    </p>

    <h2 id="interview" class="text-xl mt-6 mb-2">Teil 2: Medikamente zu einem Interview hinzufügen</h2>
    <p>
      Teil 2 wird über den Button "Interview durchführen" erreicht.
      Hier wird eine von Ihnen gewählte Probanden-ID verlangt.
      Nun sehen Sie eine Medikationsübersicht des Patienten über die gesamte Studie.
      Hier haben Sie die Möglichkeit, ein Interview durchzuführen oder zu bearbeiten.
    </p>
    <p>
      Sie haben die Möglichkeit, über den Button "Medikationsübernahme" die Medikamente <strong>des letzten abgeschlossenen Events</strong> zu übernehmen.
    </p>

    <h3 id="suche" class="text-lg mt-4 mb-2">Funktionsweise der Medikamentensuche</h3>
    <p>
      Die Suchfunktion ermöglicht eine flexible und intelligente Suche nach Arzneimitteln.
      Hier sind alle wichtigen Features und Tipps, wie man optimale Ergebnisse erhält:
    </p>

    <h4 class="text-base underline mt-4 mb-2">Freitextsuche</h4>
    <p>
      Sie können ein oder mehrere Wörter eingeben.
      Die Suche findet Medikamente, deren Name oder Eigenschaften diese Begriffe enthalten.
    </p>
    <p>
      Beispiele:
    </p>
    <ul class="list-disc list-outside ml-6">
      <li><span class="example">Aspirin</span></li>
      <li><span class="example">Ibuprofen 600</span></li>
    </ul>

    <h4 class="text-base underline mt-4 mb-2">Exakte Wortgruppen mit Anführungszeichen</h4>
    <p>
      Wenn mehrere Wörter genau in der eingegebenen Reihenfolge zusammenhängend vorkommen sollen, setzen Sie sie in Anführungszeichen.
    </p>
    <p>Beispiele:</p>
    <ul class="list-disc list-outside ml-6">
      <li><span class="example">"Acidum folicum"</span></li>
      <li><span class="example">"Metoprolol succinat"</span></li>
      <li><span class="example">Metoprolol "10 mg"</span></li>
    </ul>
    <p>
      Das ist besonders hilfreich, wenn Wörter sonst getrennt oder in anderer Reihenfolge vorkommen könnten.
    </p>

    <h4 class="text-base underline mt-4 mb-2">Mehrere Begriffe – auch getrennt möglich</h4>
    <p>
      Sie können mehrere Suchbegriffe eingeben.
      Die Suche bewertet, wie gut ein Medikament zu den Begriffen passt (Relevanz-Rangliste).
    </p>
    <p>Beispiele:</p>
    <ul class="list-disc list-outside ml-6">
      <li><span class="example">ibuprofen schmerz</span></li>
      <li><span class="example">paracetamol 500</span></li>
    </ul>
    <p>Relevanzsortierung:</p>
    <ul class="list-disc list-outside ml-6">
      <li>Wörter, die am Anfang des Namens stehen, erhöhen die Relevanz.</li>
      <li>Vollständige Treffer des gesamten Suchbegriffs werden höher bewertet.</li>
      <li>Treffende Groß-/Kleinschreibung erhöht die Relevanz:</li>
      <li class="ml-4"><span class="example">ibuprofen</span> kann auch Dexibuprofen finden.</li>
      <li class="ml-4"><span class="example">Ibuprofen</span> (mit groß geschriebenem I) dagegen wird aber immer dem klassischen Ibuprofen eine höhere Relevanz zuteilen.</li>
    </ul>

    <h4 class="text-base underline mt-4 mb-2">Mindestlänge der Suchbegriffe</h4>
    <ul class="list-disc list-outside ml-6">
      <li>Wörter mit weniger als 3 Zeichen werden ignoriert.</li>
      <li>Beispiel: Bei <span class="example">Calcium 500 mg</span> wird nur <span class="example">500</span> berücksichtigt – aber <span class="example">mg</span> nicht.</li>
      <li>Um hier bessere Treffer zu erreichen am besten Anführungszeichen verwenden, um kurze Wörter zu längeren Suchtermen zu verbinden: <span class="example">Calcium "500 mg"</span></li>
    </ul>

    <h2 id="export" class="text-xl mt-6 mb-2">Teil 3: Daten einer Studie exportieren</h2>
    <p>
      Teil 3, den <strong>Datenexport</strong>, erreichen Sie, wie die Verwaltung der Studien, über den Button "Studienverwaltung" von der Landingpage aus.
    </p>
    <p>
      Des weiteren können Sie sich über die Breadcrumbs, am oberen Bildschirmrand, zu den jeweiligen vorher besuchten Seiten klicken
    </p>

    <p>
      Für Admins oder Technikinteressierte finden Sie hier unser <NuxtLink to="https://github.com/DZD-eV-Diabetes-Research/DZDMedLog" :external="true" target="_blank">Repository</NuxtLink>
    </p>

    <UAlert v-if="configStore.branding.supportEmail" color="sky" icon="i-heroicons-envelope" class="mt-4">
      <template #description>
        <p class="text-base">
          Wenn Sie Fragen oder Feedback haben, melden Sie sich gerne:
          <NuxtLink :to="`mailto:${configStore.branding.supportEmail}`" :external="true">
            {{ configStore.branding.supportEmail }}
          </NuxtLink>
        </p>
        <p>
          Bei Fehlerberichten bitte die untenstehenden Versionsangaben einschließen.
        </p>
      </template>
    </UAlert>

    <hr>

    <div class="text-center font-extralight">
      <p>Version: {{ configStore.versionInfo.version ?? 'Unbekannt' }}</p>
      <p>Branch: {{ configStore.versionInfo.branch ?? 'Unbekannt' }}</p>
    </div>
  </section>
</template>

<style scoped>
p ~ p {
  margin-top: 0.6rem;
}

hr {
  margin: 1rem 0;
}

.example {
  background-color: lightgray;
  padding: 0.05rem 0.25rem;
  border-radius: 0.3rem;
  border: 1px solid darkgray;
}
</style>

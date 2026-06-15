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
          label: 'Hinweise zur Medikamentensuche',
        }]"
        class="self-start"
      />

      <UDivider class="my-2" size="sm" />
      <h2 class="text-3xl font-normal mb-4">Hinweise zur Medikamentensuche</h2>
    </div>

    <p>
      Die Suchfunktion ermöglicht eine flexible und intelligente Suche nach Arzneimitteln.
      Hier sind alle wichtigen Features und Tipps, wie man optimale Ergebnisse erhält:
    </p>

    <h3 class="text-xl mt-4 mb-2">Freitextsuche</h3>
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

    <h3 class="text-xl mt-4 mb-2">Exakte Wortgruppen mit Anführungszeichen</h3>
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

    <h3 class="text-xl mt-4 mb-2">Mehrere Begriffe – auch getrennt möglich</h3>
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

    <h3 class="text-xl mt-4 mb-2">Mindestlänge der Suchbegriffe</h3>
    <ul class="list-disc list-outside ml-6">
      <li>Wörter mit weniger als 3 Zeichen werden ignoriert.</li>
      <li>Beispiel: Bei <span class="example">Calcium 500 mg</span> wird nur <span class="example">500</span> berücksichtigt – aber <span class="example">mg</span> nicht.</li>
      <li>Um hier bessere Treffer zu erreichen am besten Anführungszeichen verwenden, um kurze Wörter zu längeren Suchtermen zu verbinden: <span class="example">Calcium "500 mg"</span></li>
    </ul>
  </section>
</template>

<style scoped>
p ~ p {
  margin-top: 0.6rem;
}

.example {
  background-color: lightgray;
  padding: 0.05rem 0.25rem;
  border-radius: 0.3rem;
  border: 1px solid darkgray;
}
</style>

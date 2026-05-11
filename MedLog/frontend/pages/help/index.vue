<script setup lang="ts">
const configStore = useConfigStore();
</script>

<template>
  <section class="container w-11/12 lg:w-8/12 xl:w-6/12 mx-auto mt-8">
    <h1 class="text-4xl font-normal text-center mb-4">Hilfe zu DZDMedLog</h1>

    <p class="my-4 text-center text-gray-500">
      Wählen Sie eines der Themengebiete, um mehr zu erfahren.
    </p>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <ULink to="/help/interviews">
        <UCard class="border border-gray-400 hover:bg-gray-100">
          <div class="flex flex-row items-center gap-2">
            <UIcon name="i-heroicons-clipboard-document-check" class="w-8 h-8" />
            Interview durchführen
          </div>
        </UCard>
      </ULink>
      <ULink to="/help/search">
        <UCard class="border border-gray-400 hover:bg-gray-100">
          <div class="flex flex-row items-center gap-2">
            <UIcon name="i-heroicons-magnifying-glass" class="w-8 h-8" />
            Hinweise zur Medikamentensuche
          </div>
        </UCard>
      </ULink>
      <ULink to="/help/manage-studies">
        <UCard class="border border-gray-400 hover:bg-gray-100">
          <div class="flex flex-row items-center gap-2">
            <UIcon name="i-heroicons-clipboard-document-list" class="w-8 h-8" />
            Studienverwaltung
          </div>
        </UCard>
      </ULink>
      <ULink to="/help/manage-users">
        <UCard class="border border-gray-400 hover:bg-gray-100">
          <div class="flex flex-row items-center gap-2">
            <UIcon name="i-heroicons-users" class="w-8 h-8" />
            Kontoverwaltung
          </div>
        </UCard>
      </ULink>
      <ULink to="/help/export">
        <UCard class="border border-gray-400 hover:bg-gray-100">
          <div class="flex flex-row items-center gap-2">
            <UIcon name="i-heroicons-cloud-arrow-down" class="w-8 h-8" />
            Datenexport
          </div>
        </UCard>
      </ULink>
    </div>

    <hr>

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

    <div class="text-center font-extralight mt-4">
      <p>Version: {{ configStore.versionInfo.version ?? 'Unbekannt' }}</p>
      <p>Branch: {{ configStore.versionInfo.branch ?? 'Unbekannt' }}</p>
    </div>

    <hr>

    <UAlert
        icon="i-heroicons-lock-open-solid"
        color="teal"
        variant="solid"
        title="DZDMedLog ist freie Software"
        description="Der Quellcode wurde unter der MIT-Lizenz veröffentlicht und ist auf GitHub zu finden."
        :actions="[{
          label: 'GitHub',
          variant: 'solid',
          color: 'white',
          to: 'https://github.com/DZD-eV-Diabetes-Research/DZDMedLog',
          external: true,
          target: '_blank',
          icon: 'i-heroicons-arrow-top-right-on-square',
        }]"
    />
  </section>
</template>

<style scoped>
p ~ p {
  margin-top: 0.6rem;
}

hr {
  margin: 1rem 0;
}
</style>

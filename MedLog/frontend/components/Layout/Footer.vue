<script setup lang="ts">
const configStore = useConfigStore();
const drugDbUpdaterStore = useDrugDbUpdaterStore();

</script>

<template>
  <footer class="bg-gray-100 w-full py-4">
    <div class="grid grid-cols-3 py-2 px-10 mx-auto">
      <div>
        <SystemStatus />
      </div>
      <div class="flex flex-col items-center text-sm">
        <ErrorMessage
            v-if="drugDbUpdaterStore.status?.last_update_run_error"
            title="Letztes Update der Arzneimitteldatenbank nicht erfolgreich"
            :message="drugDbUpdaterStore.status.last_update_run_error"
        />
        <template v-else>
          <div>
            <span class="font-medium">Arzneimitteldatenbank:</span> {{ configStore.drugData.sourceName ?? 'N/A' }}
          </div>
          <template v-if="drugDbUpdaterStore.status?.update_running">
            <UProgress animation="swing" :max="['Update läuft']" size="sm" color="amber" class="mt-1 w-72 object-center" />
          </template>
          <template v-else-if="drugDbUpdaterStore.status?.last_update_run_datetime_utc">
            <div>
              <span class="font-medium">Version:</span> {{ drugDbUpdaterStore.status?.current_drug_data_version ?? 'N/A' }}
            </div>
            <small>
              Zuletzt aktualisiert: <DateTime :datetime="drugDbUpdaterStore.status?.last_update_run_datetime_utc"/>
            </small>
          </template>
        </template>
      </div>
      <div class="text-end">
        <NuxtLink to="/help">Hilfe</NuxtLink>
        <NuxtLink to="https://www.dzd-ev.de/impressum" :external="true" target="_blank">Impressum</NuxtLink>
      </div>
    </div>
  </footer>
</template>

<style scoped>
a ~ a {
  margin-left: 0.7rem;
}
</style>

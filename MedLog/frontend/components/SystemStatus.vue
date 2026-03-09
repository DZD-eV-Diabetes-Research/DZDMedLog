<script setup lang="ts">
const drugDbUpdaterStore = useDrugDbUpdaterStore();
const healthCheckStore = useHealthCheckStore();

const isDegraded = computed(() => {
  // TODO define degraded condition
  return false;
});
const isCritical = computed(() => {
  // TODO define error condition
  return false;
});
</script>

<template>
  <UPopover mode="hover" :ui="{ trigger: 'w-auto' }" :popper="{ placement: 'top', arrow: true }">
    <div>
      <span class="font-medium">Status: </span> <StatusBadge :value="!isCritical" :degraded="isDegraded" />
    </div>

    <template #panel>
      <div class="p-4">
        <dl>
          <dt>Gesamtzustand:</dt>
          <dd><StatusBadge :value="healthCheckStore.healthy" /></dd>
        </dl>
        <UDivider label="Anwendung" />
        <dl>
          <dt>Datenbank bereit:</dt>
          <dd><StatusBadge :value="healthCheckStore.fullReport?.db_working" /></dd>
          <dt>Suchindex funktionsfähig:</dt>
          <dd><StatusBadge :value="healthCheckStore.fullReport?.drug_search_index_working" /></dd>
          <dt>Arzneimittel importiert:</dt>
          <dd><StatusBadge :value="healthCheckStore.fullReport?.drugs_imported" /></dd>
          <dt>Worker zuletzt erfolgreich:</dt>
          <dd><StatusBadge :value="healthCheckStore.fullReport?.last_worker_run_succesfull" /></dd>
        </dl>
        <UDivider label="Arzneimittel-Datenbank" />
        <dl>
          <dt>Einsatzbereit:</dt>
          <dd><StatusBadge :value="drugDbUpdaterStore.status?.current_drug_data_ready_to_use" /></dd>
        </dl>
      </div>
    </template>
  </UPopover>
</template>

<style scoped>
dl {
  display: grid;
  grid-template-columns: max-content auto;
}

dt {
  grid-column-start: 1;
  padding: 0.2em 0.4em 0.2em 0.6em;
  font-weight: 500;
}

dd {
  grid-column-start: 2;
  padding: 0.2em 0.6em 0.2em 0.4em;
  text-align: end;
}
</style>

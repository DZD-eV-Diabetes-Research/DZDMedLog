<script setup lang="ts">
const modelValue = defineModel<boolean>();
const emit = defineEmits<{
  start: [hasTakenMeds: boolean];
  cancel: []
}>()
</script>

<template>
  <DZDUIModal
      v-model="modelValue"
      title="Eingangsfrage"
      :ui="{ width: 'w-full sm:max-w-lg lg:max-w-xl' }"
      @cancel="$emit('cancel')"
  >
    <div>
      <p>
        Wir möchten Ihre Einnahme von Diabetes-Medikamenten in den vergangenen 12 Monaten erfassen.
        Dazu gehören sowohl Tabletten als auch Insulinpräparate.
      </p>
      <p>
        Außerdem bitten wir Sie um Angabe, welche anderen Medikamente Sie innerhalb der letzten 7 Tage eingenommen haben.
        Bitte denken Sie auch an Schmerzmittel und vom Arzt erhaltene Spritzen.
        Geben Sie Depotmittel an, auch wenn Sie diese zuletzt vor mehr als 7 Tagen eingenommen oder bekommen haben.
      </p>

      <UAlert title="Nur bei Frauen" variant="soft" color="blue" class="mt-4">
        <template #description>
          <p>
            Denken Sie bitte auch an Medikamente wie die Pille, Hormon&shy;ersatz&shy;präparate, Depotmittel oder die Spirale, auch wenn Sie diese zuletzt vor mehr als 7 Tagen eingenommen oder bekommen haben.
          </p>
        </template>
      </UAlert>

      <p>
        <strong>Haben Sie Diabetes-Medikamente in den vergangenen 12 Monaten bzw. andere Medikamente in den letzten 7 Tagen eingenommen?</strong>
      </p>

      <div class="grid grid-cols-3 gap-2 mt-4">
        <div class="flex flex-col gap-1 items-center text-center">
          <UButton label="Abbrechen" size="lg" color="gray" @click="emit('cancel')"/>
          <small>Interview nicht starten</small>
        </div>
        <div class="flex flex-col gap-1 items-center text-center">
          <UButton label="Nein" size="lg" color="amber" @click.once="emit('start', false)"/>
          <small>Interview direkt abschließen</small>
        </div>
        <div class="flex flex-col gap-1 items-center text-center">
          <UButton label="Ja" size="lg" color="emerald" @click.once="emit('start', true)"/>
          <small>Interview starten</small>
        </div>
      </div>
    </div>
  </DZDUIModal>
</template>

<style scoped>
p ~ p {
  margin-top: 1rem;
}
</style>

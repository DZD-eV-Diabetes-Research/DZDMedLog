<template>
  <UModal v-model="editModalVisibility">
    <div class="p-4">
      <div style="text-align: center;">
        <IntakeQuestion />
        <div v-if="drugStore.item">
          <br>
          <p>Medikament: {{ drugStore.item.item.name }}</p>
          <p>PZN: {{ drugStore.item.pzn }}</p>
          <p>Packungsgroesse: {{ drugStore.item.item.packgroesse }}</p>
        </div>
        <UForm @submit="onSubmit" :state="editState" :schema="editSchema" class="space-y-4">
          <UFormGroup label="Dosis" style="border-color: red;">
            <UInput type="number" v-model="editState.dose" name="dose" color="blue" />
          </UFormGroup>
          <UFormGroup label="Einnahme (Datum)">
            <UInput type="date" v-model="editState.time" name="time" color="blue" />
          </UFormGroup>
          <URadioGroup v-model="editState.selected" legend="Wurden heute Medikamente eingenommen?" name="selected"
            :options="editOptions" />
          <UButton type="submit" label="Bearbeiten" color="blue" variant="soft"
            class="border border-blue-500 hover:bg-blue-300 hover:border-white hover:text-white" />
        </UForm>
      </div>
    </div>
  </UModal>
</template>

<script setup lang="ts">
import { object, string, date, number, type InferType } from 'yup'
import type { FormSubmitEvent } from '#ui/types'

const drugStore = useDrugStore()

const editModalVisibility = ref(true)

const editSchema = object({
  selected: string().required("Required"),
  time: date().required("Required"),
  dose: number().min(0, "Hallo"),
})

type Schema = InferType<typeof schema>

const editState = reactive({
  selected: "Yes",
  time: null,
  dose: null
})


const editOptions = [{
  value: "Yes",
  label: 'Ja'
}, {
  value: "No",
  label: 'Nein',
}, {
  value: "UNKNOWN",
  label: "Unbekannt"
}]

async function onSubmit(event: FormSubmitEvent<Schema>) {
  // Do something with event.data
  const body = {
    pharmazentralnummer: drugStore.item.pzn,
    custom_drug_id: null,
    intake_start_time_utc: editState.time,
    intake_end_time_utc: null,
    administered_by_doctor: "prescribed",
    intake_regular_or_as_needed: "regular",
    dose_per_day: editState.dose,
    regular_intervall_of_daily_dose: "regular",
    as_needed_dose_unit: null,
    consumed_meds_today: editState.selected
  }

  console.log(body)
  console.log(drugStore.item.item);
  
}
</script>
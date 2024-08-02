<template>
  <div style="text-align: center" v-if="!drugStore.item && !initialLoad && !props.custom">
    <br />
    <p style="color: red">Es muss ein Medikament ausgewählt werden</p>
  </div>
  <UForm
    @submit="saveIntake()"
    :state="state"
    :schema="schema"
    class="space-y-4"
  >
    <div style="padding-top: 2.5%">
      <div v-if="props.custom">
        <div style="text-align: center" v-if="!props.edit">
          <h4>
            Hiermit wird einmalig ein Medikament angelegt, das in der
            Medikamentensuche nicht gefunden wurde
          </h4>
        </div>
        <UFormGroup label="Name" name="name" required>
          <UInput v-model="state.name" color="yellow" />
        </UFormGroup>
        <UFormGroup label="Darreichungsform" name="darrform" required>
          <h5 v-if="showDarrFormError" style="color: red">
            Darreichungsform wird benötigt
          </h5>
          <UCommandPalette
            v-if="!selectedDosageForm"
            v-model="selectedDosageForm"
            :autoselect="false"
            :groups="[{ key: 'dosageFormTable', commands: dosageFormTable }]"
            :fuse="{ resultLimit: 5, fuseOptions: { threshold: 0.2 } }"
          />
          <p v-else @click="selectedDosageForm = null" class="selectedDarrForm" style="margin-bottom:2%">
            {{ selectedDosageForm.label }}
          </p>
        </UFormGroup>
        <UAccordion :items="customDrugForm" color="yellow">
          <template #custom-form>
            <UFormGroup label="PZN" name="pzn">
              <UInput
                v-model="state.pzn"
                placeholder="Falls bekannt"
                color="yellow"
              />
            </UFormGroup>
            <UFormGroup label="Herstellercode" name="herstellerCode">
              <UInput
                v-model="state.herstellerCode"
                placeholder="Falls bekannt"
                color="yellow"
              />
            </UFormGroup>
            <UFormGroup label="Applikationsform" name="appform">
              <UInput
                v-model="state.appform"
                placeholder="Falls bekannt"
                color="yellow"
              />
            </UFormGroup>
            <UFormGroup label="ATC-Code" name="atc_code">
              <UInput
                v-model="state.atc_code"
                placeholder="Falls bekannt"
                color="yellow"
              />
            </UFormGroup>
            <UFormGroup label="Packungsgroesse" name="packgroesse">
              <UInput
                v-model="state.packgroesse"
                placeholder="Falls bekannt"
                color="yellow"
              />
            </UFormGroup>
          </template>
        </UAccordion>
        <br />
      </div>
      <UFormGroup label="Quelle der Arzneimittelangabe">
        <USelect
          v-model="selectedSourceItem"
          :options="sourceItems"
          :color="props.color"
        />
      </UFormGroup>
    </div>
    <UFormGroup label="Einnahme regelmäßig oder nach Bedarf?">
      <USelect
        v-model="selectedFrequency"
        :options="frequency"
        :color="props.color"
      />
    </UFormGroup>
    <div class="flex-container">
      <UFormGroup
        label="Dosis pro Einnahme"
        style="border-color: red"
        name="dose"
      >
        <UInput
          type="number"
          v-model="state.dose"
          :disabled="selectedFrequency !== 'regelmäßig'"
          :color="selectedFrequency !== 'regelmäßig' ? 'gray' : props.color"
        />
      </UFormGroup>
      <UFormGroup label="Intervall der Tagesdosen">
        <USelect
          v-model="state.intervall"
          :options="intervallOfDose"
          :disabled="selectedFrequency !== 'regelmäßig'"
          :color="selectedFrequency !== 'regelmäßig' ? 'gray' : props.color"
        />
      </UFormGroup>
    </div>
    <div class="flex-container">
      <UFormGroup label="Einnahme Beginn (Datum)" name="startTime">
        <UInput type="date" v-model="state.startTime" :color="props.color" />
      </UFormGroup>
      <UFormGroup label="Einnahme Ende (Datum)" name="endTime">
        <UInput type="date" v-model="state.endTime" :color="props.color" />
      </UFormGroup>
    </div>
    <URadioGroup
      v-model="state.selected"
      legend="Wurden heute Medikamente eingenommen?"
      name="selected"
      :options="options"
      :color="props.color"
    />
    <div style="text-align: center">
    <UButton
      type="submit"
      :label="props.label"
      :color="props.color"
      variant="soft"
      :class="buttonClass"
    />
  </div>
  </UForm>
</template>



<script setup lang="ts">
import dayjs from "dayjs";
import { object, number, date, string, type InferType } from "yup";

const route = useRoute();
const tokenStore = useTokenStore();
const drugStore = useDrugStore();
const initialLoad = ref(true);
const runtimeConfig = useRuntimeConfig();

const props = defineProps<{
  color?: string;
  edit?: boolean;
  custom?: boolean;
  label?: string;
  row?: any;
}>();

const buttonClass = computed(() => {
  const color = props.color;
  return `border border-${color}-500 hover:bg-${color}-300 hover:border-white hover:text-white`;
});

const state = reactive({
  selected: "Yes",
  startTime: dayjs(Date()).format("YYYY-MM-DD"),
  endTime: null,
  dose: 0,
  intervall: null,
  pzn: "",
  name: "",
  herstellerCode: "",
  darrform: "",
  appform: "",
  atc_code: "",
  packgroesse: 0,
});

const schema = object({
  selected: string().required("Required"),
  startTime: date().required("Required"),
  dose: number().min(0, "Required"),
  pzn: string(),
  name: string(),
  herstellerCode: string(),
  darrform: string(),
  appform: string(),
  atc_code: string(),
  packgroesse: number(),
});

type Schema = InferType<typeof schema>;

const sourceItems = [
  "Probandenangabe",
  "Medikamentenpackung: PZN gescannt",
  "Medikamentenpackung: PZN getippt",
  "Medikamentenpackung: Arzneimittelname",
  "Beipackzettel",
  "Medikamentenplan",
  "Rezept",
  "Nacherhebung: Tastatureingabe der PZN",
  "Nacherhebung: Arzneimittelname",
];
const selectedSourceItem = ref(sourceItems[0]);

const frequency = ["nach Bedarf", "regelmäßig"];
const selectedFrequency = ref(frequency[0]);

const intervallOfDose = [
  "unbekannt",
  "täglich",
  "jeden 2. Tag",
  "jeden 3. Tag",
  "jeden 4. Tag = 2x pro Woche",
  "Im Abstand von 1 Woche und mehr",
];
const selectedInterval = ref(intervallOfDose[0]);

const options = [
  {
    value: "Yes",
    label: "Ja",
  },
  {
    value: "No",
    label: "Nein",
  },
  {
    value: "UNKNOWN",
    label: "Unbekannt",
  },
];

const tempDose = ref();
const tempIntervall = ref();

async function saveIntake() {

  drugStore.action = false;
  initialLoad.value = false;
  tempDose.value = null;
  tempIntervall.value = null;

  drugStore.source = useDrugSourceTranslator(null, selectedSourceItem.value);
  if (selectedFrequency.value === "nach Bedarf") {
    drugStore.frequency = "as needed";
  } else {
    drugStore.frequency = "regular";
  }
  drugStore.dose = state.dose;
  tempDose.value = drugStore.dose;
  drugStore.intervall = useIntervallDoseTranslator(null, state.intervall);
  tempIntervall.value = state.intervall;
  drugStore.option = state.selected;
  drugStore.intake_start_time_utc = state.startTime;
  drugStore.intake_end_time_utc = state.endTime;
  drugStore.consumed_meds_today = state.selected;

  if (props.edit && !props.custom) {
    try {
      drugStore.editVisibility = false;
      const frequency = ref();

      if (drugStore.frequency === "nach Bedarf") {
        frequency.value = "as needed";
      } else {
        frequency.value = "regular";
      }

      const fetchBody = {
        pharmazentralnummer: drugStore.custom ? null : drugStore.item.pzn,
        source_of_drug_information: drugStore.source,
        custom_drug_id: drugStore.custom
          ? drugStore.item.item.ai_dataversion_id
          : null,
        intake_start_time_utc: drugStore.intake_start_time_utc,
        intake_end_time_utc: drugStore.intake_end_time_utc,
        administered_by_doctor: "prescribed",
        intake_regular_or_as_needed: frequency.value,
        dose_per_day: drugStore.dose,
        regular_intervall_of_daily_dose: drugStore.intervall,
        as_needed_dose_unit: null,
        consumed_meds_today: drugStore.consumed_meds_today,
      };

      await $fetch(
        `${runtimeConfig.public.baseURL}study/${route.params.study_id}/interview/${route.params.interview_id}/intake/${drugStore.editId}`,
        {
          method: "PATCH",
          headers: { Authorization: "Bearer " + tokenStore.access_token },
          body: fetchBody,
        }
      );
    } catch (error) {
      console.log(error);
    }
  } else if (!props.edit  && !props.custom) {

    await useCreateIntake(
      route.params.study_id,
      route.params.interview_id,
      drugStore.item.pzn,
      drugStore.source,
      drugStore.intake_start_time_utc,
      drugStore.intake_end_time_utc,
      drugStore.frequency,
      drugStore.intervall,
      drugStore.dose,
      drugStore.consumed_meds_today,
      null
    );
  } 

  else if (props.custom && !props.edit) {

    const response = await $fetch(
      `${runtimeConfig.public.baseURL}drug/user-custom`,
      {
        method: "POST",
        headers: { Authorization: "Bearer " + tokenStore.access_token },
        body: {
          created_at: date,
          pzn: state.pzn ? state.pzn : null,
          name: state.name ? state.name : null,
          hersteller_code: state.herstellerCode ? state.herstellerCode : null,
          darrform: selectedDosageForm.value.darrform,
          appform: state.appform ? state.appform : null,
          atc_code: state.atc_code ? state.atc_code : null,
          packgroesse: state.packgroesse ? state.packgroesse : null,
        },
      }
    );

    const pzn = state.pzn ? state.pzn : null;

    await useCreateIntake(
      route.params.study_id,
      route.params.interview_id,
      pzn,
      drugStore.source,
      drugStore.intake_start_time_utc,
      drugStore.intake_end_time_utc,
      drugStore.frequency,
      drugStore.intervall,
      drugStore.dose,
      drugStore.consumed_meds_today,
      response.id
    );
    
    drugStore.customVisibility = false

  } else {
    // HERE COMES STUFF
  }

  drugStore.action = !drugStore.action;
}

watch(selectedFrequency, (newValue) => {
  if (newValue === "nach Bedarf") {
    drugStore.frequency = "as needed";
    tempDose.value = state.dose;
    state.dose = 0;
    tempIntervall.value = state.intervall;
    state.intervall = null;
    selectedInterval.value = null;
  } else if (!props.edit) {
    drugStore.frequency = "regular";
    state.dose = tempDose.value ? tempDose.value : 1;
    state.intervall = tempIntervall.value ? tempIntervall.value : "unbekannt";
  } else {
    state.dose = drugStore.dose;
    state.intervall = drugStore.intervall;
  }
});

//test stuff

const customDrugForm = [
  {
    label: "Zusätzliche Information",
    icon: "i-heroicons-information-circle",
    slot: "custom-form",
  },
];


const showDarrFormError = ref(false);
const selectedDosageForm = ref();
const dosageFormTable = ref();

async function getDosageForm() {
  const dosageForm = await $fetch(
    `${runtimeConfig.public.baseURL}drug/enum/darrform`,
    {
      method: "GET",
      headers: { Authorization: "Bearer " + tokenStore.access_token },
    }
  );

  dosageFormTable.value = dosageForm.items.map((item) => ({
    id: item.bedeutung + " (" + item.darrform + ")",
    label: item.bedeutung + " (" + item.darrform + ")",
    bedeutung: item.bedeutung,
    darrform: item.darrform,
  }));
}

getDosageForm();

// functioning

if (props.edit) {
  selectedSourceItem.value = drugStore.source;
  selectedFrequency.value = drugStore.frequency;
  state.dose = drugStore.dose;
  state.intervall = drugStore.intervall;
  state.startTime = drugStore.intake_start_time_utc;
  state.endTime = drugStore.intake_end_time_utc;
  state.selected = drugStore.consumed_meds_today;
}

if (props.custom && props.edit){
  state.name = drugStore.drugName
  selectedDosageForm.value = {"label":drugStore.darrForm}
}
</script>

<style scoped>
.newDrugButton {
  text-align: center;
  border-color: #a9e7bc;
  border-radius: 10px;
  background-color: white;
}

.new-drug-box {
  padding: 20px;
  border-style: solid;
  border-color: #adecc0;
  border-radius: 10px;
  border-width: 2px;
}

.tableDiv {
  border-radius: 10px;
  border-width: 2px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.26);
}

.selectedDarrForm:hover {
  color: #efc85d;
  cursor: pointer;
}

.flex-container {
  display: flex;
  gap: 16px;
}

.flex-container > * {
  flex: 1;
}

.custom-disabled {
  background-color: #c2c2c2;
  border-style: solid !important;
  border-color: white;
}

.custom-border input {
  color: sky;
  border-style: dotted !important;
  border-color: green !important;
}
</style>

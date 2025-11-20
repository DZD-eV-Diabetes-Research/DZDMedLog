<template>
  <div>
    <ErrorMessage v-if="error" :error="error" class="mb-5" />
    <div v-if="isDataLoaded">

      <!-- After the drugFieldDefinitionsObject is created we loop through each of the 4 arrays:
      attr: A free field in case of yes and no questions, boolean
      attr_ref: A predefined selection of options
      attr_multi: Multiple answers possible
      attr_multi_ref: Multiple answers of predefined selction possible
      and created inputs for each item in this array. -->

      <UForm :state="state" :validate="validate" class="space-y-4" @submit.prevent="onSubmit">
        <UFormGroup label="Name" name="customName" required class="mb-6">
          <UInput v-model="state.customName" color="yellow" />
        </UFormGroup>

        <UFormGroup v-for="code in codeSystems" :key="code.id">
          <template #label>
                    <span class="inline-flex items-center gap-1">
                      {{ code.name }}
                      <UTooltip
                          :text="code.desc || 'Keine Beschreibung'"
                          :popper="{ placement: 'right' }"
                          :ui="{ width: 'max-w-4xl' }"
                      >
                        <UIcon name="i-heroicons-question-mark-circle" class="w-4 h-4 text-yellow-500 cursor-pointer" />
                      </UTooltip>
                    </span>
          </template>

          <!-- Input oder Checkbox -->
          <UInput v-model="drugCodeState[code.id]" color="yellow" />
        </UFormGroup>

        <UFormGroup v-for="attr in drugFieldDefinitionsObject.attrs" :key="attr[1]" :name="attr[1]">
          <!-- Label-Slot: Text + Tooltip-Icon -->
          <template #label>
                    <span class="inline-flex items-center gap-1">
                      {{ attr[0] }}
                      <UTooltip :text="attr[3]" :popper="{ placement: 'right' }" :ui="{ width: 'max-w-4xl' }">
                        <UIcon name="i-heroicons-question-mark-circle" class="w-4 h-4 text-yellow-500 cursor-pointer" />
                      </UTooltip>
                    </span>
          </template>

          <!-- Input oder Checkbox -->
          <UInput
              v-if="getFormInputType(attr[2]) !== 'checkbox'" v-model="attrState[attr[1]]"
              :type="getFormInputType(attr[2])" color="yellow" />
          <UCheckbox v-else v-model="attrState[attr[1]]" color="yellow" :name="attr[1]" />
        </UFormGroup>

        <UFormGroup
            v-for="attr_ref in drugFieldDefinitionsObject.attrs_ref" :key="attr_ref[1]"
            :name="attr_ref[1]">
          <template #label>
                    <span class="inline-flex items-center gap-1">
                      {{ attr_ref[0] }}
                      <UTooltip :text="attr_ref[3]" :popper="{ placement: 'right' }" :ui="{ width: 'max-w-4xl' }">
                        <UIcon name="i-heroicons-question-mark-circle" class="w-4 h-4 text-yellow-500 cursor-pointer" />
                      </UTooltip>
                    </span>
          </template>
          <USelectMenu
              v-model="attr_refState[attr_ref[1]]"
              v-model:query="queries[attr_ref[1]]"
              :options="refSelectMenus.find(item => item.field_name === attr_ref[1])?.options"
              value-attribute="value" option-attribute="display" color="yellow"
              placeholder="Option auswählen" :searchable="!!attr_ref[4]" />
        </UFormGroup>
        <UFormGroup
            v-for="attr_multi in drugFieldDefinitionsObject.attrs_multi" :key="attr_multi[1]"
            :name="attr_multi[1]">
          <template #label>
                    <span class="inline-flex items-center gap-1">
                      {{ attr_multi[0] }}
                      <UTooltip :text="attr_multi[3]" :popper="{ placement: 'right' }" :ui="{ width: 'max-w-4xl' }">
                        <UIcon name="i-heroicons-question-mark-circle" class="w-4 h-4 text-yellow-500 cursor-pointer" />
                      </UTooltip>
                    </span>
          </template>
          <UInput
              v-model="inputValues[attr_multi[1]]" placeholder="Option auswählen und Enter drücken"
              color="yellow" @keydown.enter.prevent="updateMultiState(attr_multi[1])"
              @blur="updateMultiState(attr_multi[1])" />
          <UBadge
              v-for="(word, index) in attr_multiState[attr_multi[1]]" :key="index"
              class="mr-2 cursor-pointer" color="yellow" @click="removeItem(attr_multi[1], index)">
            {{ word }}
          </UBadge>
        </UFormGroup>
        <UFormGroup
            v-for="attr_multi_ref in drugFieldDefinitionsObject.attrs_multi_ref"
            :key="attr_multi_ref[1]" :name="attr_multi_ref[1]">
          <template #label>
            <span class="inline-flex items-center gap-1">
              {{ attr_multi_ref[0] }}
              <UTooltip :text="attr_multi_ref[3]" :popper="{ placement: 'right' }" :ui="{ width: 'max-w-4xl' }">
                <UIcon name="i-heroicons-question-mark-circle" class="w-4 h-4 text-yellow-500 cursor-pointer" />
              </UTooltip>
            </span>
          </template>
          <USelectMenu
              v-model="attr_multi_refState[attr_multi_ref[1]]"
              :options="multiRefSelectMenus.find(item => item.field_name === attr_multi_ref[1])?.options"
              value-attribute="value" option-attribute="display" multiple searchable color="yellow"
              placeholder="Option auswählen">
            <template #label>
              <span
                  v-if="Array.isArray(attr_multi_refState[attr_multi_ref[1]]) && attr_multi_refState[attr_multi_ref[1]].length">
                {{attr_multi_refState[attr_multi_ref[1]].map(val => multiRefSelectMenus.find(item =>
                  item.field_name ===
                  attr_multi_ref[1])?.options.find(option => option.value === val)?.display || val)
                  .join('; ')}}
              </span>
              <span v-else>Mehrfachauswahl möglich</span>
            </template>
          </USelectMenu>
        </UFormGroup>

        <hr>
        <div class="flex justify-between">
          <UButton label="Abbrechen" variant="outline" @click.prevent="$emit('cancel')" />
          <UButton type="submit" label="Speichern" />
        </div>
      </UForm>
    </div>
    <div v-else>
      loading
    </div>
  </div>
</template>

<script setup lang="ts">
import {apiGetFieldDefinitions} from "~/api/drug";
import type {FormError} from "#ui/types";
const { $medlogapi } = useNuxtApp();

const toast = useToast();
const drugFields = useDrugFields();

interface Attribute {
  [key: string]: any;
}

export interface DrugBody {
  trade_name: string;
  market_access_date: string | null;
  market_exit_date: string | null;
  custom_drug_notes: string | null;
  attrs: Attribute[] | null;
  attrs_ref: Attribute[] | null;
  attrs_multi: Attribute[] | null;
  attrs_multi_ref: Attribute[] | null;
  codes: Attribute[] | null;
}

const emit = defineEmits(['cancel', 'save'])

const codeSystems = ref([])
const error = ref();

const state = reactive({
  customName: "",
});

const isDataLoaded = ref(false);
let drugFieldDefinitionsObject: any = null;

const drugCodeState = reactive<Record<string, string>>({});

const attrState = ref(null);
const attr_refState = reactive<Record<string, string | number | boolean>>({});
const attr_multiState = reactive({});
const attr_multi_refState = reactive<Record<string, string | number | boolean>>({});
const refSelectMenus = ref<{ field_name: string, options: { value: string, display: string }[] }[]>([]);
const multiRefSelectMenus = ref<{ field_name: string, options: { value: string, display: string }[] }[]>([]);
const inputValues = reactive({});

function validate(state: any): FormError[] {
  const errors = []

  if (!state.customName) {
    errors.push({ path: "customName", message: "Please enter a name" });
  }

  return errors
}

async function onSubmit() {
  const drugCodeBody =  Object.entries(drugCodeState).map(([key, value]) => ({
    code_system_id: key,
    code: value,
  }));

  const customDrugBody: DrugBody = {
    trade_name: state.customName,
    market_access_date: null,
    market_exit_date: null,
    custom_drug_notes: null,
    attrs: Object.entries(attrState.value).map(([key, value]) => ({ field_name: key, value: value == null ? null : String(value) })),
    attrs_ref: Object.entries(attr_refState).map(([key, value]) => ({ field_name: key, value: value })),
    attrs_multi: Object.entries(attr_multiState).map(([key, value]) => ({ field_name: key, values: value })),
    attrs_multi_ref: Object.entries(attr_multi_refState).map(([key, value]) => ({ field_name: key, values: value })),
    codes: drugCodeBody
  }

  emit('save', customDrugBody)
}

async function createRefSelectMenus(refs: any[], state: any, selectMenus: any, multiple = false) {
  try {
    for (const ref of refs) {

      const item = { field_name: ref[1], options: [] };
      let response = null

      // this leads back to the /api/drug.ts file the ref[4] is the boolean if the field_def is: 'is_large_reference_list'
      if (ref[4]) {
        response = await $medlogapi(`/api/drug/field_def/{ref}/refs?limit=10`, {
          path: {
            ref: ref[1]
          }
        });
      } else {
        response = await $medlogapi(`/api/drug/field_def/{ref}/refs`, {
          path: {
            ref: ref[1]
          }
        });

      }

      item.options = response.items.map((element) => ({
        value: element.value,
        display: element.display,
      }));

      selectMenus.value.push(item);
      state[ref[1]] = multiple ? [] : null;
    }
  } catch (error) {
    throw new Error("Could not create refSelectMenus", { cause: error });
  }
}

// Logic for the search field and function

const queries = reactive<Record<string, string>>({});

watch(
    () => ({ ...queries }),
    (newQueries) => {
      for (const [field, q] of Object.entries(newQueries)) {
        if (q && q.length >= 2) {
          onSearchRef(field, q);
        }
      }
    },
    { deep: true }
);

async function onSearchRef(fieldName: string, query: string) {
  try {
    const response = await $medlogapi(`/api/drug/field_def/{ref}/refs?search_term=${query}&limit=10`, {
      path: { ref: fieldName }
    });

    const menu = refSelectMenus.value.find(item => item.field_name === fieldName);
    if (menu) {
      menu.options = response.items.map((el: any) => ({
        value: el.value,
        display: el.display,
      }));
    }
  } catch (err) {
    toast.add({
      title: "Fehler bei der Suche",
      description: err.value.data?.detail ?? err.message ?? err,
    });
  }
}

// end of search logic

async function createMultiState() {
  drugFieldDefinitionsObject.attrs_multi.forEach(element => {
    attr_multiState[element[1]] = [];
    inputValues[element[1]] = "";
  });
}

function updateMultiState(field) {
  const newValues = inputValues[field]
      .split(',')
      .map(w => w.trim())
      .filter(w => w !== "");

  attr_multiState[field].push(...newValues);
  inputValues[field] = "";
}

const fetchFieldDefinitions = async () => {
  drugFieldDefinitionsObject = await apiGetFieldDefinitions("dynamic_form");
  attrState.value = reactive(generateDynamicState(drugFieldDefinitionsObject.attrs));
  //schema.value = object(generateDynamicSchema(drugFieldDefinitionsObject));
  isDataLoaded.value = true;
  await createRefSelectMenus(drugFieldDefinitionsObject.attrs_ref, attr_refState, refSelectMenus)
  await createRefSelectMenus(drugFieldDefinitionsObject.attrs_multi_ref, attr_multi_refState, multiRefSelectMenus, true)
  await createMultiState()
}

function generateDynamicState(fieldsObject: [[]]) {
  const dynamicState = {};

  fieldsObject.forEach(([, key, type]) => {
    dynamicState[key] = type === "BOOL" ? false : null;
  });
  return dynamicState;
}

function getFormInputType(type: any) {
  switch (type) {
    case "STR":
      return "text";
    case "INT":
      return "number";
    case "FLOAT":
      return "number";
    case "BOOL":
      return "checkbox";
    case "DATETIME":
      return "date";
    case "DATE":
      return "date";
    default:
      return "text";
  }
}

function removeItem(field, index) {
  attr_multiState[field].splice(index, 1);
}

onMounted(async () => {
  try {
    await fetchFieldDefinitions()
    codeSystems.value = drugFields.codes
    codeSystems.value?.forEach(code => {
      drugCodeState[code.id] = "";
    });
  } catch (e) {
    error.value = e;
  }
});

</script>

<style scoped>

</style>

<template>
  <div>
    <ErrorMessage v-if="error" :error="error" class="mb-5" />
    <div v-if="isDataLoaded">

      <UForm :state="state" :validate="validate" class="space-y-4" @submit.prevent="onSubmit">
        <UFormGroup label="Name" name="customName" required class="mb-6">
          <UInput v-model="state.customName" />
        </UFormGroup>

        <DZDUIFormGroup v-for="code in codeSystems" :key="code.id" :label="code.name" :description="code.desc ?? ''">
          <UInput v-model="drugCodeState[code.id]" />
        </DZDUIFormGroup>

        <DZDUIFormGroup
            v-for="attr in drugFields.fieldsForCustomDrugs.attrs"
            :key="attr.field_name"
            :name="attr.field_name"
            :label="attr.field_name_display"
            :description="attr.field_desc ?? ''"
        >
          <UInput
              v-if="getFormInputType(attr.value_type) !== 'checkbox'"
              v-model="attrState[attr.field_name] as string|number"
              :type="getFormInputType(attr.value_type)"
          />
          <UCheckbox v-else v-model="attrState[attr.field_name] as boolean" :name="attr.field_name" />
        </DZDUIFormGroup>

        <DZDUIFormGroup
            v-for="attr_ref in drugFields.fieldsForCustomDrugs.attrs_ref"
            :key="attr_ref.field_name"
            :name="attr_ref.field_name"
            :label="attr_ref.field_name_display"
            :description="attr_ref.field_desc ?? ''"
        >
          <USelectMenu
              v-model="attr_refState[attr_ref.field_name]"
              v-model:query="queries[attr_ref.field_name]"
              :options="refSelectMenus.find(item => item.field_name === attr_ref.field_name)?.options"
              value-attribute="value"
              option-attribute="display"
              placeholder="Option auswählen"
              :searchable="!!attr_ref.is_large_reference_list"
          />
        </DZDUIFormGroup>

        <DZDUIFormGroup
            v-for="attr_multi in drugFields.fieldsForCustomDrugs.attrs_multi"
            :key="attr_multi.field_name"
            :name="attr_multi.field_name"
            :label="attr_multi.field_name_display"
            :description="attr_multi.field_desc ?? ''"
        >
          <UInput
              v-model="inputValues[attr_multi.field_name]"
              placeholder="Option auswählen und Enter drücken"
              @keydown.enter.prevent="updateMultiState(attr_multi.field_name)"
              @blur="updateMultiState(attr_multi.field_name)"
          />
          <UBadge
              v-for="(word, index) in attr_multiState[attr_multi.field_name]"
              :key="index"
              class="mr-2 cursor-pointer"
              @click="removeItem(attr_multi.field_name, index)"
          >
            {{ word }}
          </UBadge>
        </DZDUIFormGroup>

        <DZDUIFormGroup
            v-for="attr_multi_ref in drugFields.fieldsForCustomDrugs.attrs_multi_ref"
            :key="attr_multi_ref.field_name"
            :name="attr_multi_ref.field_name"
            :label="attr_multi_ref.field_name_display"
            :description="attr_multi_ref.field_desc ?? ''"
        >
          <USelectMenu
              v-model="attr_multi_refState[attr_multi_ref.field_name]"
              :options="multiRefSelectMenus.find(item => item.field_name === attr_multi_ref.field_name)?.options"
              value-attribute="value" option-attribute="display" multiple searchable
              placeholder="Option auswählen">
            <template #label>
              <span
                  v-if="Array.isArray(attr_multi_refState[attr_multi_ref.field_name]) && attr_multi_refState[attr_multi_ref.field_name].length">
                {{attr_multi_refState[attr_multi_ref.field_name].map(val => multiRefSelectMenus.find(item =>
                  item.field_name ===
                  attr_multi_ref.field_name)?.options.find(option => option.value === val)?.display || val)
                  .join('; ')}}
              </span>
              <span v-else>Mehrfachauswahl möglich</span>
            </template>
          </USelectMenu>
        </DZDUIFormGroup>

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
import type {FormError} from "#ui/types";
import type {SchemaDrugAttrFieldDefinitionContainer, SchemaDrugCodeSystem, SchemaDrugCustomCreate} from "#open-fetch-schemas/medlogapi";
const { $medlogapi } = useNuxtApp();

const toast = useToast();
const drugFields = useDrugFields();

interface FieldOptions {
  field_name: string;
  options: { value: string, display: string }[];
}

const emit = defineEmits<{
  cancel: []
  save: [customDrugBody: SchemaDrugCustomCreate]
}>()

const codeSystems = ref<SchemaDrugCodeSystem[]>([])
const error = ref();

const state = reactive({
  customName: "",
});

const isDataLoaded = ref(false);

const drugCodeState = reactive<Record<string, string>>({});

const attrState = reactive<Record<string, string | number | boolean>>({});
const attr_refState = reactive<Record<string, string | number | boolean>>({});
const attr_multiState = reactive<Record<string, string[]>>({});
const attr_multi_refState = reactive<Record<string, string[]>>({});
const refSelectMenus = ref<FieldOptions[]>([]);
const multiRefSelectMenus = ref<FieldOptions[]>([]);
const inputValues = reactive<Record<string, string>>({});

function validate(state: any): FormError[] {
  const errors = []

  if (!state.customName) {
    errors.push({ path: "customName", message: "Please enter a name" });
  }

  return errors
}

async function onSubmit() {
  const drugCodeBody =  Object.entries(drugCodeState)
      .map(([key, value]) => ({
        code_system_id: key,
        code: value,
      })).filter(item => item.code !== '');

  const customDrugBody: SchemaDrugCustomCreate = {
    trade_name: state.customName,
    market_access_date: null,
    market_exit_date: null,
    custom_drug_notes: null,
    attrs: Object.entries(attrState).map(([key, value]) => ({ field_name: key, value: !value ? null : String(value) })),
    attrs_ref: Object.entries(attr_refState).map(([key, value]) => ({ field_name: key, value: value == null ? null : String(value) })),
    attrs_multi: Object.entries(attr_multiState).map(([key, value]) => ({ field_name: key, values: value })),
    attrs_multi_ref: Object.entries(attr_multi_refState).map(([key, value]) => ({ field_name: key, values: value })),
    codes: drugCodeBody
  }

  emit('save', customDrugBody)
}

async function createRefSelectMenus(refs: SchemaDrugAttrFieldDefinitionContainer['attrs_ref'] | SchemaDrugAttrFieldDefinitionContainer['attrs_multi_ref'], state: Record<string, any>, selectMenus: Ref<FieldOptions[]>, multiple = false) {
  try {
    for (const ref of refs) {

      const item = { field_name: ref.field_name, options: [] };
      let response = null

      if (ref.is_large_reference_list) {
        response = await $medlogapi('/api/drug/field_def/{field_name}/refs', {
          path: {
            field_name: ref.field_name
          },
          query: {
            limit: 10,
          },
        });
      } else {
        response = await $medlogapi('/api/drug/field_def/{field_name}/refs', {
          path: {
            field_name: ref.field_name
          }
        });

      }

      item.options = response.items.map((element) => ({
        value: element.value,
        display: element.display,
      }));

      selectMenus.value.push(item);
      state[ref.field_name] = multiple ? [] : null;
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
    const response = await $medlogapi('/api/drug/field_def/{field_name}/refs', {
      path: {
        field_name: fieldName
      },
      query: {
        search_term: query,
        limit: 10,
      },
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
  drugFields.fieldsForCustomDrugs.attrs_multi.forEach(element => {
    attr_multiState[element.field_name] = [];
    inputValues[element.field_name] = "";
  });
}

function updateMultiState(fieldName: string) {
  const newValues = inputValues[fieldName]
      .split(',')
      .map(w => w.trim())
      .filter(w => w !== "");

  attr_multiState[fieldName].push(...newValues);
  inputValues[fieldName] = "";
}

const fetchFieldDefinitions = async () => {
  generateDynamicState(drugFields.fieldsForCustomDrugs.attrs);
  isDataLoaded.value = true;
  await createRefSelectMenus(drugFields.fieldsForCustomDrugs.attrs_ref, attr_refState, refSelectMenus)
  await createRefSelectMenus(drugFields.fieldsForCustomDrugs.attrs_multi_ref, attr_multi_refState, multiRefSelectMenus, true)
  await createMultiState()
}

function generateDynamicState(fieldsObject: SchemaDrugAttrFieldDefinitionContainer['attrs']): void {
  fieldsObject.forEach((attr) => {
    attrState[attr.field_name] = attr.value_type === "BOOL" ? false : "";
  });
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

function removeItem(field: string, index: number) {
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

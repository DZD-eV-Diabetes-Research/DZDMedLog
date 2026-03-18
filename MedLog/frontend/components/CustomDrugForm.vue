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
          <RefFieldSelectMenu
              v-model="attr_refState[attr_ref.field_name]"
              :field-definition="attr_ref"
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
          <RefFieldSelectMenu
              v-model="attr_multi_refState[attr_multi_ref.field_name]"
              :field-definition="attr_multi_ref"
              multiple
          />
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

const drugFields = useDrugFields();

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

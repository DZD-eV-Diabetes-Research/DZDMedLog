<template>
  <div>
    <ErrorMessage v-if="error" :error="error" class="mb-5" />
    <div v-if="isDataLoaded">

      <UForm :state="state" :validate="validate" class="space-y-4" @submit.prevent="onSubmit">
        <UFormGroup label="Name" name="customName" required class="mb-6">
          <UInput v-model="state.customName" />
        </UFormGroup>

        <DZDUIFormGroup v-for="code in drugFields.codes" :key="code.id" :label="code.name" :description="code.desc ?? ''">
          <UInput v-model="drugCodeState[code.id]" />
        </DZDUIFormGroup>

        <DZDUIFormGroup
          v-for="field in prioritizedFieldDefinitions"
          :key="field.fieldDefinition.field_name"
          :name="field.fieldDefinition.field_name"
          :label="field.fieldDefinition.field_name_display"
          :description="field.fieldDefinition.field_desc ?? ''"
        >
          <InputTags
            v-if="isMultiValueField(field.fieldDefinition)"
            v-model="attr_multiState[field.fieldDefinition.field_name]"
          />
          <RefFieldSelectMenu
            v-else-if="isSingleRefField(field.fieldDefinition)"
            v-model="attr_refState[field.fieldDefinition.field_name]"
            :field-definition="field.fieldDefinition"
          />
          <RefFieldSelectMenu
            v-else-if="isMultiRefField(field.fieldDefinition)"
            v-model="attr_multi_refState[field.fieldDefinition.field_name]"
            :field-definition="field.fieldDefinition"
            multiple
          />
          <UCheckbox
            v-else-if="getFormInputType(field.fieldDefinition.value_type) === 'checkbox'"
            v-model="attrState[field.fieldDefinition.field_name] as boolean"
            :name="field.fieldDefinition.field_name"
          />
          <UInput
            v-else
            v-model="attrState[field.fieldDefinition.field_name] as string|number"
            :type="getFormInputType(field.fieldDefinition.value_type)"
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
import type {SchemaDrugCustomCreate} from "#open-fetch-schemas/medlogapi";
import {computed} from "#imports";
import {isMultiRefField, isMultiValueField, isSingleRefField} from "~/type-helper";

const drugFields = useDrugFields();

const emit = defineEmits<{
  cancel: []
  save: [customDrugBody: SchemaDrugCustomCreate]
}>()

const attrState = reactive<Record<string, string | number | boolean>>({});
const attr_refState = reactive<Record<string, string | number | boolean>>({});
const attr_multiState = reactive<Record<string, string[]>>({});
const attr_multi_refState = reactive<Record<string, string[]>>({});
const drugCodeState = reactive<Record<string, string>>({});
const error = ref();
const isDataLoaded = ref(false);
const state = reactive({
  customName: "",
});

const prioritizedFieldDefinitions = computed(() => {
  const fieldDefinitions = useGetPrioritizedFieldDefinitions(drugFields.fieldsForCustomDrugs);
  return Array.of(...fieldDefinitions[1], ...fieldDefinitions[2], ...fieldDefinitions[3]);
});

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
    attrs_ref: Object.entries(attr_refState).map(([key, value]) => ({ field_name: key, value: !value ? null : String(value) })),
    attrs_multi: Object.entries(attr_multiState).map(([key, value]) => ({ field_name: key, values: value })),
    attrs_multi_ref: Object.entries(attr_multi_refState).map(([key, value]) => ({ field_name: key, values: value })),
    codes: drugCodeBody
  }

  emit('save', customDrugBody)
}

function initializeState() {
  drugFields.codes.forEach(code => {
    drugCodeState[code.id] = "";
  });
  drugFields.fieldsForCustomDrugs.attrs.forEach((attr) => {
    attrState[attr.field_name] = attr.value_type === "BOOL" ? false : "";
  });
  drugFields.fieldsForCustomDrugs.attrs_ref.forEach(element => {
    attr_refState[element.field_name] = "";
  });
  drugFields.fieldsForCustomDrugs.attrs_multi.forEach(element => {
    attr_multiState[element.field_name] = [];
  });
  drugFields.fieldsForCustomDrugs.attrs_multi_ref.forEach(element => {
    attr_multi_refState[element.field_name] = [];
  });
}

function getFormInputType(type: string) {
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

onMounted(async () => {
  try {
    initializeState();
    isDataLoaded.value = true;
  } catch (e) {
    error.value = e;
  }
});
</script>

<style scoped>

</style>

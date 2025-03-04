<template>
  <Layout>
    <div v-if="isDataLoaded">
      <UForm :state="state" class="space-y-4" @submit="onSubmit">
        <UFormGroup v-for="attr in drugFieldDefinitionsObject.attrs" :label="attr[0]" :name="attr[1]" :key="attr[1]">
          <UInput v-if="getFormInputType(attr[2]) !== 'checkbox'" v-model="state[attr[1]]"
            :type="getFormInputType(attr[2])" />
          <UCheckbox v-else v-model="state[attr[1]]" :label="String(state[attr[1]])" :name="state[attr[0]]"
            :ui="{ background: 'blue' }" />
        </UFormGroup>
        <UFormGroup v-for="attr_ref in drugFieldDefinitionsObject.attrs_ref" :label="attr_ref[0]" :name="attr_ref[1]"
          :key="attr_ref[1]">
          <USelectMenu v-model="attr_refState[attr_ref[1]]"
            :options="refSelectMenus.find(item => item.field_name === attr_ref[1])?.options" value-attribute="value"
            option-attribute="display" />
        </UFormGroup>
        <UFormGroup v-for="attr_multi in drugFieldDefinitionsObject.attrs_multi" :label="attr_multi[0]"
          :name="attr_multi[1]" :key="attr_multi[1]">
          <UInput placeholder="Enter a value and press Enter" v-model="inputValues[attr_multi[1]]"
            @keydown.enter.prevent="updateMultiState(attr_multi[1])" @blur="updateMultiState(attr_multi[1])" />
          <UBadge v-for="(word, index) in attr_multiState[attr_multi[1]]" :key="index" class="mr-2 cursor-pointer"
            @click="removeItem(attr_multi[1], index)">
            {{ word }}
          </UBadge>
        </UFormGroup>
        <UFormGroup v-for="attr_multi_ref in drugFieldDefinitionsObject.attrs_multi_ref" :label="attr_multi_ref[0]"
          :name="attr_multi_ref[1]" :key="attr_multi_ref[1]">
          <USelectMenu v-model="attr_multi_refState[attr_multi_ref[1]]"
            :options="multiRefSelectMenus.find(item => item.field_name === attr_multi_ref[1])?.options"
            value-attribute="value" option-attribute="display" multiple searchable>
            <template #label>
              <span
                v-if="Array.isArray(attr_multi_refState[attr_multi_ref[1]]) && attr_multi_refState[attr_multi_ref[1]].length">
                {{attr_multi_refState[attr_multi_ref[1]].map(val => multiRefSelectMenus.find(item => item.field_name ===
                  attr_multi_ref[1])?.options.find(option => option.value === val)?.display || val)
                  .join('; ')}}
              </span>
              <span v-else>Choose your fighter</span>
            </template>
          </USelectMenu>
        </UFormGroup>
        <UButton type="submit">
          Submit
        </UButton>
      </UForm>
    </div>
    <div v-else>
      loading
    </div>
  </Layout>
</template>

<script setup lang="ts">

import { onMounted, ref, reactive } from "vue";
import { object, number, date, string, type InferType, boolean } from "yup";
import { apiGetFieldDefinitions } from '~/api/drug';
const runTimeConfig = useRuntimeConfig();
const tokenStore = useTokenStore();

const isDataLoaded = ref(false);
let drugFieldDefinitionsObject: any = null;

const state = ref(null);
const schema = ref(null);

const attr_refState = reactive<Record<string, string | number | boolean>>({});
const attr_multiState = reactive({});
const attr_multi_refState = reactive<Record<string, string | number | boolean>>({});
const refSelectMenus = ref<{ field_name: string, options: { value: string, display: string }[] }[]>([]);
const multiRefSelectMenus = ref<{ field_name: string, options: { value: string, display: string }[] }[]>([]);
const inputValues = reactive({});

async function createRefSelectMenus(refs: any[], state: any, selectMenus: any, multiple = false) {
  try {
    for (const ref of refs) {
      let item = { field_name: ref[1], options: [] };

      const response = await $fetch(`${runTimeConfig.public.baseURL}v2/drug/field_def/${ref[1]}/refs`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${tokenStore.access_token}`,
        },
      });

      item.options = response.items.map((element) => ({
        value: element.value,
        display: element.display,
      }));

      selectMenus.value.push(item);
      state[ref[1]] = multiple ? [] : item.options[0]?.value;
    }
  } catch (error) {
    console.error("Create refSelectMenus Error:", error);
  }
}

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

function removeItem(field, index) {
  attr_multiState[field].splice(index, 1);
}

const fetchFieldDefinitions = async () => {
  try {
    drugFieldDefinitionsObject = await apiGetFieldDefinitions("dynamic_form");
    state.value = reactive(generateDynamicState(drugFieldDefinitionsObject));
    schema.value = object(generateDynamicSchema(drugFieldDefinitionsObject));
    isDataLoaded.value = true;
    createRefSelectMenus(drugFieldDefinitionsObject.attrs_ref, attr_refState, refSelectMenus)
    createRefSelectMenus(drugFieldDefinitionsObject.attrs_multi_ref, attr_multi_refState, multiRefSelectMenus, true)
    createMultiState()

  } catch (error) {
    console.error("Error fetching field definitions:", error);
  }
};

function generateDynamicState(fieldsObject) {
  const dynamicState = {};
  Object.values(fieldsObject).forEach((fieldGroup) => {
    fieldGroup.forEach(([label, key, type]) => {
      dynamicState[key] = type === "BOOL" ? false : null;
    });
  });
  return dynamicState;
}

function generateDynamicSchema(fieldsObject) {
  const dynamicSchema = {};
  Object.values(fieldsObject).forEach((fieldGroup) => {
    fieldGroup.forEach(([label, key, type]) => {
      dynamicSchema[key] = getSchemaForType(type);
    });
  });
  return dynamicSchema;
}

function getSchemaForType(type: any) {
  switch (type) {
    case "STR":
      return string();
    case "INT":
      return number().integer();
    case "FLOAT":
      return number();
    case "BOOL":
      return boolean();
    case "DATETIME":
      return date();
    case "DATE":
      return date();
    default:
      return string();
  }
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

function onSubmit() {
  console.log(state);
  console.log(attr_refState);
}

onMounted(fetchFieldDefinitions);

</script>
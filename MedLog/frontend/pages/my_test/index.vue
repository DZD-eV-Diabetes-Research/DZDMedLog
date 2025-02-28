<template>
  <Layout>
    {{ state }}
    <br>
    <br>
    <!-- {{ schema }} -->
    <br>
    <br>
    <!-- {{ drugFieldDefinitionsObject.attrs }} -->
    <br>
    <br>
    <div v-if="isDataLoaded">
      <UForm :state="state" class="space-y-4" @submit="onSubmit">
        <!-- <UFormGroup v-for="attr in drugFieldDefinitionsObject.attrs" :label="attr[0]" :name="attr[1]" :key="attr[1]">
          <UInput v-if="getFormInputType(attr[2]) !== 'checkbox'" v-model="state[attr[1]]"
            :type="getFormInputType(attr[2])" />
          <UCheckbox v-else v-model="state[attr[1]]" :label="String(state[attr[1]])" :name="state[attr[0]]"
            :ui="{ background: 'blue' }" />
        </UFormGroup> -->
        <UFormGroup v-for="attr_ref in drugFieldDefinitionsObject.attrs_ref" :label="attr_ref[0]" :name="attr_ref[1]"
          :key="attr_ref[1]">
          <USelectMenu v-model="attr_refState[attr_ref[1]]" :options="selectMenus.find(item => item.field_name === attr_ref[1])?.options" value-attribute="value"
            option-attribute="display" />
        </UFormGroup>
        <!-- <UFormGroup v-for="attr_multi in drugFieldDefinitionsObject.attrs_multi" :label="attr_multi[0]"
          :name="attr_multi[1]" :key="attr_multi[1]">
          <UInput placeholder="test" v-model="state[attr_multi[1]]" :type="getFormInputType(attr_multi[2])" />
        </UFormGroup>
        <UFormGroup v-for="attr_multi_ref in drugFieldDefinitionsObject.attrs_multi_ref" :label="attr_multi_ref[0]"
          :name="attr_multi_ref[1]" :key="attr_multi_ref[1]">
          <UInput placeholder="test" v-model="state[attr_multi_ref[1]]" :type="getFormInputType(attr_multi_ref[2])" />
        </UFormGroup> -->
        <UButton type="submit">
          Submit
        </UButton>
      </UForm>
    </div>
    <div v-else>
      loading
    </div>
    {{ attr_refState }}
    <!-- {{ drugFieldDefinitionsObject.attrs_ref }} -->
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
const selectMenus = ref<{ field_name: string, options: { value: string, display: string }[] }[]>([]);

async function createSelectMenus(refs: any[]) {
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
      attr_refState[ref[1]] = item.options[0].value
    }
  } catch (error) {
    console.error("Create SelectMenus Error:", error);
  }
}



const fetchFieldDefinitions = async () => {
  try {
    drugFieldDefinitionsObject = await apiGetFieldDefinitions("dynamic_form");
    state.value = reactive(generateDynamicState(drugFieldDefinitionsObject));
    schema.value = object(generateDynamicSchema(drugFieldDefinitionsObject));
    isDataLoaded.value = true;
    createSelectMenus(drugFieldDefinitionsObject.attrs_ref)


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

}

onMounted(fetchFieldDefinitions);

</script>
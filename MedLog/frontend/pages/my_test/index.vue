<template>
  <UIBaseCard>
    <div style="text-align: center;">
      <!-- <h4 style="color:red">Sie löschen folgenden Eintrag: </h4>
      <br>
      <h4>{{ drugToDelete.drug }}</h4>
      <br>
      <p style="color: red">PZN: {{ drugToDelete.pzn }}</p>
      <br> -->
      <UForm :schema="deleteSchema" :state="deleteState" class="space-y-4" @submit="onSubmit">
        <UFormGroup label="Zum löschen die PZN eintragen" name="pzn">
          <UInput v-model="deleteState.pzn" color="red" :placeholder="drugToDelete.pzn" />
        </UFormGroup>
        <br>
        <UButton type="submit" color="red" variant="soft"
          class="border border-red-500 hover:bg-red-300 hover:border-white hover:text-white">
          Eintrag löschen
        </UButton>
      </UForm>
    </div>
  </UIBaseCard>
  
  <UIBaseCard>
    <UForm :schema="schema" :state="state" class="space-y-4" @submit="onSubmit2">
    <UFormGroup label="Email" name="email">
      <UInput v-model="state.email" />
    </UFormGroup>

    <UFormGroup label="Password" name="password">
      <UInput v-model="state.password" type="password" />
    </UFormGroup>

    <UButton type="submit">
      Submit
    </UButton>
  </UForm>
  </UIBaseCard>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { object, string, type InferType } from "yup";
import type { FormSubmitEvent } from "#ui/types";

const deleteSchema = object({
  pzn: string().required('Required').test('is-dynamic-value', 'PZN muss übereinstimmen', function (value) {
    return value == drugToDelete.pzn;
  }),
});

type DeleteSchema = InferType<typeof deleteSchema>;

const deleteState = reactive({
  pzn: '',
});

const deleteModalVisibility = ref(true);
const drugToDelete = reactive({ drug: "hallo", pzn: "1234" });

async function onSubmit(event: FormSubmitEvent<DeleteSchema>) {
  // Do something with event.data
  console.log(event.data)
}

const schema = object({
  email: string().email('Invalid email').required('Required'),
  password: string()
    .min(8, 'Must be at least 8 characters')
    .required('Required')
})

type Schema = InferType<typeof schema>

const state = reactive({
  email: undefined,
  password: undefined
})

async function onSubmit2 (event: FormSubmitEvent<Schema>) {
  // Do something with event.data
  console.log(event.data)
}
</script>

<template>
  <Layout>
    <UIBaseCard>
      <button @click="download()">Download this</button>
    </UIBaseCard>
    <UIBaseCard>
      <button @click="openModal()">Modal</button>
    </UIBaseCard>
    <UModal v-model="modalVisibility">
      <div class="p-4">
        <h3>This is my favourite Modal</h3>
        <UFormGroup label="Email">
          <UInput placeholder="you@example.com" icon="i-heroicons-envelope" />
        </UFormGroup>
        <UAccordion :items="customDrugForm" variant="link" :ui="customAccordionUI">
          <template #custom-form>
            <UFormGroup label="Email" description="We'll only use this for spam.">
              <UInput placeholder="you@example.com" icon="i-heroicons-envelope" />
            </UFormGroup>
          </template>
        </UAccordion>
      </div>
    </UModal>
  </Layout>
</template>

<script setup lang="ts">
const studyId = "b77b0e8b-85c0-429f-b2c0-7e617aebf682";

const customDrugForm = [{
  label: "Zusätzliche Information",
  icon: "i-heroicons-information-circle",
  slot: "custom-form",
}];

const customAccordionUI = {
  item: {
    color: 'text-blue-500 dark:text-blue-400'
  }
};

async function download() {
  console.log(studyId);
}

const modalVisibility = ref(false);

async function openModal() {
  modalVisibility.value = !modalVisibility.value;
}
</script>

<style scoped>
/* Add any additional scoped styles here */
</style>

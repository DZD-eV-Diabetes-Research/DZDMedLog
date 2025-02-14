<!-- <template>
  <div class="p-4">
    <UForm
      :schema="newDrugSchema"
      :state="newDrugState"
      class="space-y-4"
      @submit="createNewDrug"
    >
      <div style="text-align: center">
        <h4>
          Hiermit wird einmalig ein Medikament angelegt, das in der
          Medikamentensuche nicht gefunden wurde
        </h4>
      </div>
      <UFormGroup label="Name" name="name" required>
        <UInput v-model="newDrugState.name" color="yellow" />
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
        <p v-else @click="selectedDosageForm = null" class="selectedDarrForm">
          {{ selectedDosageForm.label }}
        </p>
      </UFormGroup>
      <UAccordion :items="customDrugForm" color="yellow">
        <template #custom-form>
          <UFormGroup label="Dosis" name="dose">
            <UInput v-model="newDrugState.dose" color="yellow" />
          </UFormGroup>
          <UFormGroup label="PZN" name="pzn">
            <UInput
              v-model="newDrugState.pzn"
              placeholder="Falls bekannt"
              color="yellow"
            />
          </UFormGroup>
          <UFormGroup label="Herstellercode" name="herstellerCode">
            <UInput
              v-model="newDrugState.herstellerCode"
              placeholder="Falls bekannt"
              color="yellow"
            />
          </UFormGroup>
          <UFormGroup label="Applikationsform" name="appform">
            <UInput
              v-model="newDrugState.appform"
              placeholder="Falls bekannt"
              color="yellow"
            />
          </UFormGroup>
          <UFormGroup label="ATC-Code" name="atc_code">
            <UInput
              v-model="newDrugState.atc_code"
              placeholder="Falls bekannt"
              color="yellow"
            />
          </UFormGroup>
          <UFormGroup label="Packungsgroesse" name="packgroesse">
            <UInput
              v-model="newDrugState.packgroesse"
              placeholder="Falls bekannt"
              color="yellow"
            />
          </UFormGroup>
        </template>
      </UAccordion>
      <div style="text-align: center">
        <UButton
          type="submit"
          color="yellow"
          variant="soft"
          class="border border-yellow-500 hover:bg-yellow-300 hover:border-white hover:text-white"
        >
          Ungelistetes Medikament Speichern
        </UButton>
      </div>
    </UForm>
  </div>
  <DrugForm color="yellow" :edit=false :custom=true label="U"/>
</template> -->

<script setup lang="ts">
const test = "1"
</script>

<style scoped></style>

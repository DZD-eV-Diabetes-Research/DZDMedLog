<script setup lang="ts">
import { type InferType, object, string } from "yup";
import { probandExternalIdNormalizationOptions } from "~/constants";
import type {SchemaProbandExternalIdNormalization} from "#open-fetch-schemas/medlogapi";

const toast = useToast();

const props = defineProps({
  normalization: { type: String as () => SchemaProbandExternalIdNormalization, default: "none" },
  pattern: { type: String, default: "" },
})

defineEmits<{
  cancel: []
  confirm: [pattern: string, normalization: SchemaProbandExternalIdNormalization]
}>()

const loading = ref(false);
const patternMatches = ref<boolean|undefined>(undefined)
const patternValid = ref<boolean|undefined>(undefined)
const patternSafe = ref<boolean|undefined>(undefined)

const state = reactive<RegExTestFormSchema>({
  pattern: "",
  value: "",
  normalization: "none"
});

const schema = object({
  pattern: string().max(1024),
  value: string().max(256).required("Ein Testwert ist erforderlich"),
  normalization: string().oneOf(probandExternalIdNormalizationOptions.map(item => item.value)).required(),
});

export type RegExTestFormSchema = InferType<typeof schema>;

async function testPattern(pattern: string|undefined, value: string, normalization?: SchemaProbandExternalIdNormalization) {
  loading.value = true;

  const { data, error } = await useMedlogapi('/api/proband-external-id/validate-pattern', {
    method: 'POST',
    body: {
      pattern: pattern,
      sample: value,
      normalization: normalization
    }
  })

  if (error.value) {
    loading.value = false;
    toast.add({
      title: "Konnte Prüfung nicht ausführen",
      description: useGetErrorMessage(error.value),
    });
    return
  }

  patternValid.value = data.value?.pattern_compiles;
  patternSafe.value = data.value?.pattern_safe;
  patternMatches.value = data.value?.valid;
  loading.value = false;
}

onMounted(async () => {
  state.pattern = props.pattern;
  state.normalization = props.normalization;
})

let debounceTimeout: NodeJS.Timeout | undefined = undefined;

watch(
    [() => state.pattern, () => state.value, () => state.normalization],
    ([newPattern, newValue, newNormalization]) => {
      if (debounceTimeout !== undefined) {
        clearTimeout(debounceTimeout);
        debounceTimeout = undefined;
      }

      // Empty search is executed immediately
      if (newValue === "") {
        testPattern(newPattern, newValue, newNormalization);
        return;
      }

      // Otherwise wait a bit for more input, so we are not sending a query for every keystroke
      debounceTimeout = setTimeout(testPattern, 500, newPattern, newValue, newNormalization);
    },
    { immediate: false }
);
</script>

<template>
  <UModal :ui="{ width: 'lg:max-w-2xl' }" prevent-close>
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-lg">Normalisierung & Regulären Ausdruck testen</span>
          <UButton color="gray" variant="ghost" icon="i-heroicons-x-mark-20-solid" class="-my-1" @click="$emit('cancel')" />
        </div>
      </template>

      <p class="mb-4 text-gray-500 text-sm">
        Hier können die Einstellungen für die Normalisierung und den regulären Ausdruck interaktiv ausprobiert und am Schluss in das Formular übernommen werden.
      </p>

      <div class="flex flex-row gap-2 justify-between">
        <UForm :state="state" :schema="schema" class="space-y-4">
          <UFormGroup
              label="Normalisierung"
              name="normalization"
          >
            <USelect v-model="state.normalization" :options="probandExternalIdNormalizationOptions" />
          </UFormGroup>

          <UFormGroup
              label="Regulärer Ausdruck"
              name="pattern"
          >
            <UInput v-model.trim="state.pattern" type="text">
              <template #leading>^</template>
              <template #trailing>$</template>
            </UInput>
          </UFormGroup>

          <UFormGroup
              label="Zu testende ID"
              name="value"
          >
            <UInput v-model.trim="state.value" type="text" icon="i-heroicons-hashtag-solid" :loading="loading" />
          </UFormGroup>
        </UForm>

        <UDivider orientation="vertical" icon="i-heroicons-arrow-right-circle" />

        <div class="self-center">
          <dl>
            <dt>Ausdruck gültig</dt>
            <dd><StatusBadge :value="patternValid" fail-label="Nein" ok-label="Ja" /></dd>
            <dt>Ausdruck sicher</dt>
            <dd><StatusBadge :value="patternSafe" fail-label="Nein" ok-label="Ja" /></dd>
            <dt>Test-ID besteht Prüfung</dt>
            <dd><StatusBadge :value="patternMatches" fail-label="Nein" ok-label="Ja" /></dd>
          </dl>
        </div>
      </div>

      <div class="flex flex-row justify-between mt-4">
        <UButton
            label="Abbrechen"
            color="gray"
            class="px-6"
            @click="$emit('cancel')"
        />
        <UButton
            label="Übernehmen"
            :color="patternValid && patternSafe && patternMatches ? 'green' : 'amber'"
            class="px-6"
            :disabled="loading"
            @click="$emit('confirm', state.pattern ?? '', state.normalization)"
        />
      </div>
    </UCard>
  </UModal>
</template>

<style scoped>
dl {
  display: grid;
  grid-template-columns: max-content auto;
}

dt {
  grid-column-start: 1;
  padding: 0.2em 0.4em 0.2em 0.6em;
}

dd {
  grid-column-start: 2;
  padding: 0.2em 0.6em 0.2em 0.4em;
  text-align: end;
}
</style>

<template>
    <div>
        <LayoutHeader />
        <UIBaseCard>
          <div class="prose" style="text-align: center;">
            <template v-if="error.statusCode === 404">
              <h1>404!</h1>
              <p>Sorry, that page doesn't exist.</p>
            </template>
            <template v-else>
              <h1>Dang</h1>
              <p>
                <strong>{{ error.message }}</strong>
              </p>
              <p>It looks like something broke.</p>
              <p>Sorry about that.</p>
              <details v-if="error.cause">
                <summary>Fehlerdetails</summary>
                {{ error.cause }}
              </details>
            </template>
            <p>
              Return to the
              <NuxtLink to="/login"> startpage.</NuxtLink>
            </p>
          </div>
        </UIBaseCard>
        <LayoutFooter />
    </div>
</template>

<script setup lang="ts">
import type { NuxtError } from '#app';

defineProps({
  error: {
    type: Object as () => NuxtError,
    required: true,
  },
})

</script>

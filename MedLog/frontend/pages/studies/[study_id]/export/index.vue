<template>
  <Layout>
    <div style="text-align: center">
      <h2>Datenexport</h2>
    </div>
    <div style="text-align: center">
      <UButton
        type="button"
        label="Download anfragen"
        color="blue"
        variant="soft"
        @click="requestDownload()"
        class="border border-blue-500 hover:bg-blue-300 hover:border-white hover:text-white"
      />
    </div>
    <div class="my-card">
      <UTable :rows="downloads" :columns="columns">
        <template #status-data="{ row }">
          <UButton
            v-if="row.status === 'success'"
            icon="i-heroicons-check"
            size="2xs"
            color="emerald"
            variant="solid"
            :ui="{ rounded: 'rounded-full' }"
            square
          />

          <UButton
            v-else
            icon="i-heroicons-arrow-path"
            size="2xs"
            color="blue"
            variant="outline"
            :ui="{ rounded: 'rounded-full' }"
            :class="{ rotating: row.status === 'queued' }"
            square
          />
        </template>
        <template #actions-data="{ row }">
          <UButton
            v-if="row.status === 'success'"
            color="gray"
            variant="ghost"
            icon="i-heroicons-arrow-down-tray"
            @click="downloadFile(row)"
          />
        </template>
      </UTable>
    </div>
  </Layout>
</template>

<script setup lang="ts">
const route = useRoute();
const tokenStore = useTokenStore();
const runtimeConfig = useRuntimeConfig();
const studyStore = useStudyStore();

const columns = [
  {
    key: "study",
    label: "Studie",
  },
  {
    key: "time",
    label: "Zeitpunkt",
  },
  {
    key: "status",
    label: "Status",
  },
  {
    key: "actions",
    label: "Download",
  },
];

const downloads = ref([]);
let downloadCheckInterval: NodeJS.Timeout | null = null;

async function getDownloads() {
  const data = await $fetch(
    `${runtimeConfig.public.baseURL}study/${route.params.study_id}/export`,
    {
      method: "GET",
      headers: { Authorization: "Bearer " + tokenStore.access_token },
    }
  );

  const studyName = await studyStore.getStudy(route.params.study_id);

  downloads.value = data.items.map((item) => ({
    study: studyName.display_name,
    time: item.created_at,
    status: item.state,
    downloadLink: `${runtimeConfig.public.baseURL}${item.download_file_path}`,
  }));

  if (!downloads.value.some(download => download.status === "queued") && downloadCheckInterval) {
    clearInterval(downloadCheckInterval);
    downloadCheckInterval = null;
  }
}

async function downloadFile(row) {
  console.log(row.downloadLink);
  const fileUrl = row.downloadLink;
  try {
    const response = await fetch(fileUrl, {
      method: "GET",
      headers: {
        Authorization: "Bearer " + tokenStore.access_token,
        Accept: "*/*",
      },
    });

    if (response.ok) {
      const a = document.createElement("a");
      a.href = fileUrl;
      a.click();
      a.remove();
    } else {
      console.error("Failed to download file:", response.statusText);
    }
  } catch (error) {
    console.error("Failed to download file:", error.message);
  }
}

async function requestDownload() {
  try {
    await $fetch(
      `${runtimeConfig.public.baseURL}study/${route.params.study_id}/export?format=csv`,
      {
        method: "POST",
        headers: { Authorization: "Bearer " + tokenStore.access_token },
      }
    );
    getDownloads();
    startDownloadCheck();

  } catch (error) {
    console.log(error);
  }
}

function startDownloadCheck() {
  if (!downloadCheckInterval) {
    downloadCheckInterval = setInterval(getDownloads, 5000); 
  }
}

getDownloads();

onBeforeUnmount(() => {
  if (downloadCheckInterval) {
    clearInterval(downloadCheckInterval);
  }
});
</script>

<style scoped>
@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(180deg);
  }
}

.rotating {
  animation: rotate 0.75s linear infinite;
}

.my-card {
  margin: 2rem auto;
  max-width: 60rem;
  padding: 1rem;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.26);
}
</style>

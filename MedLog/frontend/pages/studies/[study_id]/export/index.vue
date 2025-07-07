<template>
  <Layout>
    <div style="text-align: center">
      <h2 class="text-4xl font-normal mb-4">Datenexport</h2>
    </div>
    <div style="text-align: center">
      <UButton type="button" label="Download anfragen" color="blue" variant="soft" @click="requestDownload()"
        class="border border-blue-500 hover:bg-blue-300 hover:border-white hover:text-white" />
    </div>
    <div class="my-card">
      <UTable :rows="downloads" :columns="columns">
        <template #status-data="{ row }">
          <div v-if="row.status === 'success'">
            <UTooltip text="Export erfolgreich" :popper="{ arrow: true }">
            <UButton icon="i-heroicons-check" size="2xs" color="primary" variant="solid"
              :ui="{ rounded: 'rounded-full' }" class="no-hover" square />
            </UTooltip>
          </div>

          <div v-else-if="row.status === 'failed'">
            <UTooltip text="Export fehlgeschlagen" :popper="{ arrow: true }">
              <UButton icon="i-heroicons-x-mark" size="2xs" color="red" variant="solid"
                :ui="{ rounded: 'rounded-full' }" class="no-hover" square />
            </UTooltip>
          </div>

          <div v-else>
            <UTooltip text="Export läuft" :popper="{ arrow: true }">
              <UButton icon="i-heroicons-arrow-path" size="2xs" color="blue" variant="outline"
              :ui="{ rounded: 'rounded-full' }" :class="{ rotating: row.status === 'queued' }" class="no-hover"
              square />
            </UTooltip>

          </div>
        </template>
        <template #actions-data="{ row }">
          <UButton v-if="row.status === 'success'" color="gray" variant="ghost" icon="i-heroicons-arrow-down-tray"
            @click="downloadFile(row)" />
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
const { $api } = useNuxtApp();


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

function parseTime(time: string) {
  const date = new Date(time);
  const options = {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  };
  return date.toLocaleString('de-DE', options).replace(',', '');
}


async function listDownloads() {
  const data = await $api(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/export`);

  const studyName = await studyStore.getStudy(route.params.study_id);

  downloads.value = data.items.map((item) => ({
    study: studyName.display_name,
    time: parseTime(item.created_at),
    status: item.state,
    downloadLink: `${runtimeConfig.public.baseURL}${item.download_file_path}`,
  }));

  if (!downloads.value.some(download => download.status === "queued") && downloadCheckInterval) {
    clearInterval(downloadCheckInterval);
    downloadCheckInterval = null;
  }
}

async function downloadFile(row) {
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

// 1. The request is sent to the backend

async function requestDownload() {
  try {
    await $api(
      `${runtimeConfig.public.baseURL}study/${route.params.study_id}/export?format=csv`,
      {
        method: "POST",
      }
    );
    listDownloads();
    startDownloadCheck();

  } catch (error) {
    console.log(error);
  }
}

// 2. This checks if the backend is done and while it is not it pings the backened every 5 seconds vis the listDownloads function

function startDownloadCheck() {
  if (!downloadCheckInterval) {
    downloadCheckInterval = setInterval(listDownloads, 5000);
  }
}

listDownloads();

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

.no-hover {
  pointer-events: none;
}

.no-hover:hover {
  background-color: transparent;
  border-color: inherit;
  color: inherit;
}
</style>

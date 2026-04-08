<template>
  <section v-if="isAllowedToExport" class="container w-11/12 lg:w-8/12 xl:w-6/12 mx-auto mt-8">
    <div class="flex justify-center break-all mb-4 relative items-center">
      <div class="absolute left-0">
        <UButton
            to="/manage/studies"
            label="Zurück"
            title="Zur Studienverwaltung"
            variant="outline"
            color="gray"
            icon="i-heroicons-arrow-left-circle"
        />
      </div>
      <h1 class="text-4xl font-normal text-center w-8/12">
        Datenexport &ndash; {{ studyStore.nameForStudy(studyId) }}
      </h1>
    </div>

    <div class="flex flex-row justify-end">
      <UButton
        label="Export generieren"
        icon="i-heroicons-archive-box"
        variant="solid"
        @click="requestDownload()"
      />
    </div>
    <UTable :rows="downloads" :columns="columns">
      <template #status-data="{ row }">
        <div v-if="row.status === 'success'">
          <UTooltip text="Export erfolgreich" :popper="{ arrow: true }">
            <UButton
                icon="i-heroicons-check" size="2xs" color="primary" variant="solid"
                :ui="{ rounded: 'rounded-full' }" class="no-hover" square />
          </UTooltip>
        </div>

        <div v-else-if="row.status === 'failed'">
          <UTooltip text="Export fehlgeschlagen" :popper="{ arrow: true }">
            <UButton
                icon="i-heroicons-x-mark" size="2xs" color="red" variant="solid"
                :ui="{ rounded: 'rounded-full' }" class="no-hover" square />
          </UTooltip>
        </div>

        <div v-else>
          <UTooltip text="Export läuft" :popper="{ arrow: true }">
            <UButton
                icon="i-heroicons-arrow-path" size="2xs" color="blue" variant="outline"
                :ui="{ rounded: 'rounded-full' }" :class="{ rotating: row.status === 'queued' }" class="no-hover"
                square />
          </UTooltip>
        </div>
      </template>
      <template #actions-data="{ row }">
        <UButton
            v-if="row.status === 'success'"
            :to="row.downloadLink"
            label="Herunterladen"
            color="gray"
            variant="outline"
            icon="i-heroicons-arrow-down-tray"
            @click.prevent="downloadFile(row)" />
      </template>
    </UTable>
  </section>
  <section v-else class="container w-11/12 lg:w-8/12 xl:w-6/12 mx-auto mt-8">
    <ErrorMessage
        title="Keine Berechtigung"
        message="Ihnen fehlt die Berechtigung für diese Seite"
    />
  </section>
</template>

<script setup lang="ts">
import { useDayjs } from '#dayjs'
import localizedFormat from 'dayjs/plugin/localizedFormat'
import type {SchemaWorkerJobState} from "#open-fetch-schemas/medlogapi";

const dayjs = useDayjs();
const route = useRoute();
const studyStore = useStudyStore();
const { $medlogapi } = useNuxtApp();
const toast = useToast();
const userStore = useUserStore();

dayjs.extend(localizedFormat);

const columns = [
  {
    key: "study",
    label: "Studie",
    rowClass: 'max-w-64 break-all',
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

interface Download {
  study: string;
  time: string;
  status: SchemaWorkerJobState;
  downloadLink: string;
}

const downloads = ref<Download[]>([]);
let downloadCheckInterval: NodeJS.Timeout | null = null;

const isAllowedToExport = computed(() => {
  // TODO check for study-specific rights
  return userStore.isAdmin;
});

const studyId = computed(() => {
  return route.params.study_id as string;
});

async function listDownloads() {
  try {
    const data = await $medlogapi('/api/study/{study_id}/export', {
      path: {
        study_id: studyId.value,
      }
    });

    const study = studyStore.getStudy(studyId.value);

    downloads.value = data.items.map((item) => ({
      study: study?.display_name ?? 'N/A',
      time: dayjs.utc(item.created_at).local().format('LLL'),
      status: item.state,
      downloadLink: `${item.download_file_path}`,
    }));

    if (!downloads.value.some(download => download.status === "queued") && downloadCheckInterval) {
      clearInterval(downloadCheckInterval);
      downloadCheckInterval = null;
    }
  } catch (error) {
    toast.add({
      title: "Fehler beim Laden der Exporte",
      description: useGetErrorMessage(error),
    });
  }
}

async function downloadFile(row: Download) {
  try {
    const response = await fetch(row.downloadLink, {
      method: "GET",
    });

    if (response.ok) {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(await response.blob());

      // Try and get the file name
      const contentDisposition = response.headers.get('content-disposition');
      if (contentDisposition) {
        const parts = contentDisposition.split(';');
        if (parts.length < 1 || parts[0] !== 'attachment') {
          throw new Error('Not an attachment');
        }

        const filenameParameter = parts.find(item => item.trim().startsWith('filename='))
        if (filenameParameter) {
          const matches = filenameParameter.match(/filename="?([^"]+)"?/)
          if (matches && matches.length > 1) {
            a.download = matches[1];
          }
        }
      }

      // Trigger file download
      a.click();
      URL.revokeObjectURL(a.href);
      a.remove();
    } else {
      toast.add({
        title: "Fehler beim Herunterladen",
        description: response.statusText,
      });
    }
  } catch (error) {
    toast.add({
      title: "Fehler beim Herunterladen",
      description: useGetErrorMessage(error),
    });
  }
}

// 1. The request is sent to the backend

async function requestDownload() {
  try {
    await $medlogapi(
      '/api/study/{study_id}/export',
      {
        method: "POST",
        path: {
          study_id: studyId.value
        },
        query: {
          format: 'csv',
        },
      }
    );
  } catch (error) {
    toast.add({
      title: "Konnte Exportauftrag nicht anlegen",
      description: useGetErrorMessage(error),
    });
    return;
  }

  await listDownloads();
  startDownloadCheck();
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

:deep(td:first-child) {
  /* Override the white-space breaking for the first column  */
  white-space: unset;
}
</style>

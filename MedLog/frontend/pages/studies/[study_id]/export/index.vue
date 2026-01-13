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
            label="Herunterladen"
            color="gray"
            variant="outline"
            icon="i-heroicons-arrow-down-tray"
            @click="downloadFile(row)" />
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

const downloads = ref([]);
let downloadCheckInterval: NodeJS.Timeout | null = null;

const isAllowedToExport = computed(() => {
  // TODO check for study-specific rights
  return userStore.isAdmin;
});

const studyId = computed(() => {
  return route.params.study_id;
});

async function listDownloads() {
  try {
    const data = await $medlogapi(`/api/study/{studyId}/export`, {
      path: {
        studyId: studyId.value,
      }
    });

    const studyName = studyStore.getStudy(studyId.value);

    downloads.value = data.items.map((item) => ({
      study: studyName.display_name,
      time: dayjs.utc(item.created_at).local().format('LLL'),
      status: item.state,
      downloadLink: `${item.download_file_path}`,
    }));

    if (!downloads.value.some(download => download.status === "queued") && downloadCheckInterval) {
      clearInterval(downloadCheckInterval);
      downloadCheckInterval = null;
    }
  } catch (e) {
    toast.add({
      title: "Fehler beim Laden der Exporte",
      description: e.message,
    });
  }
}

async function downloadFile(row) {
  const fileUrl = row.downloadLink;
  console.log(fileUrl);
  try {
    const response = await fetch(fileUrl, {
      method: "GET",
    });

    if (response.ok) {
      const a = document.createElement("a");
      a.href = fileUrl;
      a.click();
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
      description: error.message,
    });
  }
}

// 1. The request is sent to the backend

async function requestDownload() {
  try {
    await $medlogapi(
      `/api/study/{studyId}/export?format=csv`,
      {
        method: "POST",
        path: {
          studyId: studyId.value
        }
      }
    );
  } catch (error) {
    toast.add({
      title: "Konnte Exportauftrag nicht anlegen",
      description: error.message,
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

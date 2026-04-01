<script setup lang="ts">
const systemAnnouncementsStore = useSystemAnnouncementsStore();
</script>

<template>
  <UPopover v-if="systemAnnouncementsStore.allAnnouncements && systemAnnouncementsStore.allAnnouncements.length" :ui="{ container: 'w-full md:w-1/2' }" overlay>
    <UButton
        color="white"
        size="xl"
        label="Systemmeldungen"
        trailing-icon="i-heroicons-chevron-down-20-solid"
    >
      <template #leading>
        <div class="flex flex-row justify-center gap-1 p-2">
          <UTooltip
              v-if="systemAnnouncementsStore.numberOfAlertAnnouncements > 0"
              text="Kritische Meldungen"
              :popper="{ arrow: true, placement: 'bottom' }"
          >
            <UBadge
                :label="systemAnnouncementsStore.numberOfAlertAnnouncements"
                icon="i-heroicons-exclamation-circle-solid"
                color="red"
            />
          </UTooltip>
          <UTooltip
              v-if="systemAnnouncementsStore.numberOfWarningAnnouncements > 0"
              text="Warnungen"
              :popper="{ arrow: true, placement: 'bottom' }"
          >
            <UBadge
                icon="i-heroicons-exclamation-triangle-solid"
                :label="systemAnnouncementsStore.numberOfWarningAnnouncements"
                color="amber"
            />
          </UTooltip>
          <UTooltip
              v-if="systemAnnouncementsStore.numberOfInfoAnnouncements > 0"
              text="Informationen"
              :popper="{ arrow: true, placement: 'bottom' }"
          >
            <UBadge
                :label="systemAnnouncementsStore.numberOfInfoAnnouncements"
                icon="i-heroicons-information-circle-solid"
                color="sky"
            />
          </UTooltip>
        </div>
      </template>
    </UButton>

    <template #panel="{ close }">
      <div class="flex flex-col gap-4 p-4">
        <SystemAnnouncement
            v-for="announcement in systemAnnouncementsStore.allAnnouncements"
            :key="announcement.id"
            :announcement="announcement"
            @dismiss="id => systemAnnouncementsStore.dismissAnnouncement(id)"
        />
        <div class="self-end">
          <UButton color="white" label="Schließen" @click="close" />
        </div>
      </div>
    </template>
  </UPopover>
</template>

<style scoped>

</style>

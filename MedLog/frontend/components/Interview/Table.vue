<script setup lang="ts">
const eventStore = useEventStore()

const props = defineProps({
  interviews: { type: Array as () => Interview, required: true },
  studyId: { type: String, required: true },
});

const columns = [{
  key: 'date',
  label: 'Datum'
}, {
  key: 'eventName',
  label: 'Event'
}, {
  key: 'actions',
  label: ''
}]

const rows = computed(() => {
  const items = props.interviews?.map((interview: Interview) => {
    return {
      date: formatDate(interview.interview_start_time_utc, true),
      timestamp: Date.parse(interview.interview_start_time_utc + 'Z').valueOf() ?? 0,
      eventId: interview.event_id,
      eventName: eventStore.nameForEvent(interview.event_id),
      interviewId: interview.id,
      probandId: interview.proband_external_id,
    }
  }) ?? [];

  // Sort descending by date
  return items.sort((a, b) => b.timestamp - a.timestamp);
})
</script>

<template>
  <UTable :rows="rows" :columns="columns">
    <template #actions-data="{ row }">
      <div class="flex flex-row justify-end">
        <UButton
            :to="`/interview/proband/${row.probandId}/study/${studyId}/event/${row.eventId}/interview/${row.interviewId}`"
            label="Zum Interview"
            variant="link"
            icon="i-heroicons-arrow-right-circle"
            trailing
        />
      </div>
    </template>
  </UTable>
</template>

<style scoped>

</style>

<script setup lang="ts">
import { useDayjs } from '#dayjs'
import localizedFormat from 'dayjs/plugin/localizedFormat'

const dayjs = useDayjs();
const eventStore = useEventStore()

dayjs.extend(localizedFormat);

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
      date: dayjs.utc(interview.interview_start_time_utc).local().format('LL'),
      timestamp: dayjs.utc(interview.interview_start_time_utc).valueOf() ?? 0,
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
            :to="`/studies/${studyId}/proband/${row.probandId}/interview/${row.interviewId}`"
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

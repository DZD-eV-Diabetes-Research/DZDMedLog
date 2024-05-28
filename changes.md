# Change in branch rewrite/feat-events-by-probant



* Interview 
  * interview_number becomes interviewer_user_id and is now a foreign key to user table.
* Event
  * Event has new attr `order_position` which is the default `order_by` attr
  * New endpoint `/study/{study_id}/proband/{proband_id}/event` which
    * Lists all event but additionally includes the `proband_id` and the number of interviews for given proband under each event `proband_interview_count`.
    * Events with zero interviews can be excluded with `exlude_empty_events` in the query params
  * New endpoint `/study/{study_id}/event/order`.
    * Provide a list of event obj or event IDs and the backend will apply a new `order_position` in sequence of the given list.
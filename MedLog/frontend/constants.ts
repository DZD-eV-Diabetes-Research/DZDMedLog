import type {
    SchemaAdministeredByDoctorAnswers,
    SchemaConsumedMedsTodayAnswers,
    SchemaIntakeEndDateOption,
    SchemaIntakeRegularOrAsNeededAnswers,
    SchemaIntakeStartDateOption,
    SchemaIntervalOfDailyDoseAnswers,
    SchemaProbandExternalIdNormalization,
    SchemaSourceOfDrugInformationAnwers
} from "#open-fetch-schemas/medlogapi";

export const drugSourceOptions: { value: SchemaSourceOfDrugInformationAnwers; label: string }[] = [
    { value: "Study participant: verbal specification", label: "Probandenangabe" },
    { value: "Medication package: Scanned PZN", label: "Medikamentenpackung: PZN gescannt" },
    { value: "Medication package: Typed in PZN", label: "Medikamentenpackung: PZN getippt" },
    { value: "Medication package: Drug name", label: "Medikamentenpackung: Arzneimittelname" },
    { value: "Medication leaflet", label: "Beipackzettel" },
    { value: "Study participant: medication plan", label: "Medikamentenplan" },
    { value: "Study participant: Medication prescription", label: "Rezept" },
    { value: "Follow up via phone/message: Typed in PZN", label: "Nacherhebung: Tastatureingabe der PZN" },
    { value: "Follow up via phone/message: Medication name", label: "Nacherhebung: Arzneimittelname" },
];

export const administeredByDoctorOptions: { value: SchemaAdministeredByDoctorAnswers; label: string }[] = [
    { value: 'prescribed', label: 'ja, auf Rezept' },
    { value: 'recommended', label: 'vom Arzt empfohlen' },
    { value: 'no', label: 'nein' },
    { value: 'unknown', label: 'unbekannt' },
];

export const frequencyOptions: { value: SchemaIntakeRegularOrAsNeededAnswers; label: string }[] = [
    { value: "as needed", label: "nach Bedarf" },
    { value: "regular", label: "regelmäßig" },
];

export const doseIntervalOptions: { value: SchemaIntervalOfDailyDoseAnswers; label: string }[] = [
    {
        value: "Unknown",
        label: "unbekannt"
    },
    {
        value: "Daily",
        label: "täglich"
    },
    {
        value: "every 2. day",
        label: "jeden 2. Tag"
    },
    {
        value: "every 3. day",
        label: "jeden 3. Tag"
    },
    {
        value: "every 4. day / twice a week",
        label: "jeden 4. Tag = 2x pro Woche"
    },
    {
        value: "intervals of one week or more",
        label: "Im Abstand von 1 Woche und mehr"
    },
    {
        value: "intervals of one month or more",
        label: "Im Abstand von 1 Monat und mehr",
    },
    {
        value: "intervals of one year or more",
        label: "Im Abstand von 1 Jahr und mehr",
    },
];

export const medsTakenTodayOptions: { value: SchemaConsumedMedsTodayAnswers; label: string }[] = [
    {
        value: "Yes",
        label: "Ja",
    },
    {
        value: "No",
        label: "Nein",
    },
    {
        value: "UNKNOWN",
        label: "Unbekannt",
    },
];

export const startDateOptions: { value: SchemaIntakeStartDateOption; label: string }[] = [
    {
        value: "at_least_12_months",
        label: "Mindestens 12 Monate",
    },
    {
        value: "unknown",
        label: "Unbekannt",
    },
];

export const endDateOptions: { value: SchemaIntakeEndDateOption; label: string }[] = [
    {
        value: "ongoing",
        label: "Wird aktuell eingenommen",
    },
    {
        value: "unknown",
        label: "Unbekannt",
    },
];

export const probandExternalIdNormalizationOptions: { value: SchemaProbandExternalIdNormalization; label: string }[] = [
    {
        value: "none",
        label: "Keine Normalisierung",
    },
    {
        value: "lowercase",
        label: "Kleinbuchstaben erzwingen",
    },
    {
        value: "uppercase",
        label: "Großbuchstaben erzwingen",
    },
];

export const plausibilityErrorMessages: { rule: string, message: string, messageTemplate?: string }[] = [
    {
        rule: "end_date_before_start_date",
        message: "Enddatum liegt vor Startdatum"
    },
    {
        rule: "start_date_in_future",
        message: "Startdatum liegt in der Zukunft"
    },
    {
        rule: "end_date_in_future",
        message: "Enddatum liegt in der Zukunft"
    },
    {
        rule: "consumed_today_with_future_start_date",
        message: "Heute eingenommen, aber Einnahme noch nicht begonnen",
        messageTemplate: "Einnahme am Tag der Untersuchung (%s) ist nicht möglich, wenn der Einnahmezeitraum erst danach beginnt",
    },
    {
        rule: "consumed_today_with_past_end_date",
        message: "Einnahme beendet, aber heute eingenommen",
        messageTemplate: "Einnahme am Tag der Untersuchung (%s) ist nicht möglich, wenn der Einnahmezeitraum bereits zuvor endete",
    },
    {
        rule: "dose_per_day_negative",
        message: "Tagesdosis muss 0 oder positive Zahl sein"
    },
    {
        rule: "start_date_implausibly_old",
        message: "Startdatum unrealistisch lange her",
        messageTemplate: "Das Datum darf nicht vor %s liegen"
    },
    {
        rule: "end_date_implausibly_old",
        message: "Enddatum unrealistisch lange her",
        messageTemplate: "Das Datum darf nicht vor %s liegen"
    },
];

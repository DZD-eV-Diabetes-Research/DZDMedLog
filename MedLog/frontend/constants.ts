import type {
    SchemaAdministeredByDoctorAnswers,
    SchemaConsumedMedsTodayAnswers,
    SchemaIntakeEndDateOption,
    SchemaIntakeRegularOrAsNeededAnswers,
    SchemaIntakeStartDateOption,
    SchemaIntervalOfDailyDoseAnswers,
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

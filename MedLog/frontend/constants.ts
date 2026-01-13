export const drugSourceOptions: { value: string; label: string }[] = [
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

export const administeredByDoctorOptions: { value: string; label: string }[] = [
    { value: 'prescribed', label: 'ja, auf Rezept' },
    { value: 'recommended', label: 'vom Arzt empfohlen' },
    { value: 'no', label: 'nein' },
    { value: 'unknown', label: 'unbekannt' },
];

export const frequencyOptions: { value: string; label: string }[] = [
    { value: "as needed", label: "nach Bedarf" },
    { value: "regular", label: "regelmäßig" },
];

export const doseIntervalOptions: { value: string; label: string }[] = [
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

export const medsTakenTodayOptions: { value: string; label: string }[] = [
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

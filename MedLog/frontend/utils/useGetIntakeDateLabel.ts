import type { SchemaIntakeDatePrecision } from "#open-fetch-schemas/medlogapi";
import useGetLabelForValue from "~/utils/useGetLabelForValue";

// Formats an intake date as ISO 8601 with reduced precision (2024-03-10, 2024-03 or 2024), matching the export.
// Falls back to the label of the date option if no date is set.
export default function (
    date: string | null | undefined,
    precision: SchemaIntakeDatePrecision | null | undefined,
    dateOptions: { value: string; label: string }[],
    option: string | null | undefined,
): string {
    if (!date) {
        return useGetLabelForValue(dateOptions, option);
    }

    if (precision === 'year') {
        return date.slice(0, 4);
    }

    if (precision === 'month') {
        return date.slice(0, 7);
    }

    return date;
}

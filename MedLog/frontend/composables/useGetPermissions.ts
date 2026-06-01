import { useMedlogapi } from "#open-fetch";
import type { SchemaStudyPermissionDesc } from "#open-fetch-schemas/medlogapi";

export default async function (): Promise<SchemaStudyPermissionDesc[]> {
    const { data, error } = await useMedlogapi('/api/study/permissions/available');

    if (error.value) {
        throw error.value;
    }

    if (!Array.isArray(data.value)) {
        throw new Error("Permissions endpoint did not provide an array");
    }

    return data.value ?? [];
}

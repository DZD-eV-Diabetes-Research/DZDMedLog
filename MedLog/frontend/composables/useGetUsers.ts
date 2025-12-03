import { useMedlogapi } from "#open-fetch";
import type { SchemaUser } from "#open-fetch-schemas/medlogapi";

export default async function (includeDeactivated: boolean): Promise<SchemaUser[]> {
    const { data, error } = await useMedlogapi('/api/user', {
        query: {
            incl_deactivated: includeDeactivated,
        },
    });

    if (error.value) {
        throw error.value;
    }

    return data.value?.items ?? [];
}

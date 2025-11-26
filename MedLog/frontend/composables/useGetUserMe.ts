import { useMedlogapi } from "#open-fetch";
import type { SchemaUser } from "#open-fetch-schemas/medlogapi";

export default async function (): Promise<SchemaUser> {
    const { data, error } = await useMedlogapi('/api/user/me');

    if (error.value) {
        throw error.value;
    }

    if (data.value === null) {
        throw new Error('No data.');
    }

    return data.value;
}

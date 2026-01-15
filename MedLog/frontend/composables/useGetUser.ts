import { useMedlogapi } from "#open-fetch";
import type { SchemaUser } from "#open-fetch-schemas/medlogapi";

export default async function (userId: string): Promise<SchemaUser> {
    const { data, error } = await useMedlogapi('/api/user/{user_id}', {
        path: {
            user_id: userId,
        },
    });

    if (error.value) {
        throw error.value;
    }

    if (!data.value) {
        throw new Error('No data returned.');
    }

    return data.value;
}

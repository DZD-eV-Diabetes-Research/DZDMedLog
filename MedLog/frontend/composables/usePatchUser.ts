import { useMedlogapi } from "#open-fetch";
import type { SchemaUser } from "#open-fetch-schemas/medlogapi";

export default async function (userId: string, body: any): Promise<SchemaUser> {
    const { data, error } = await useMedlogapi('/api/user/{user_id}', {
        method: "PATCH",
        path: {
            user_id: userId,
        },
        body,
    });

    if (error.value) {
        throw error.value;
    }

    if (!data.value) {
        throw new Error('No data returned.');
    }

    return data.value;
}

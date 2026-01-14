import {useMedlogapi} from "#open-fetch";
import type { SchemaStudy } from "#open-fetch-schemas/medlogapi";

export default async function (name:string): Promise<SchemaStudy>{
    const { data, error } = await useMedlogapi("/api/study", {
        method: "POST",
        body: {
            display_name: name,
            no_permissions: false,
        },
    })

    if (error.value) {
        throw error.value;
    }

    if (!data.value) {
        throw new Error('No data returned.');
    }

    return data.value;
}

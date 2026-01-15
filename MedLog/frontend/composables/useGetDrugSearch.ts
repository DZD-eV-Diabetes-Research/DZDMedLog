import { useMedlogapi } from "#open-fetch";
import type { SchemaPaginatedResponseMedLogSearchEngineResult } from "#open-fetch-schemas/medlogapi";

export default async function (searchTerm: string, limit = 100): Promise<SchemaPaginatedResponseMedLogSearchEngineResult> {
    const { data, error } = await useMedlogapi('/api/drug/search', {
        query: {
            offset: 0,
            limit: limit,
            search_term: searchTerm,
        },
    });

    if (error.value) {
        if (error.value.statusCode === 425) {
            throw new Error("Der Suchindex wird noch aufgebaut, daher ist die Suche derzeit noch nicht verfügbar. Bitte versuchen Sie es in Kürze erneut.")
        }
        throw error.value;
    }

    if (!data.value) {
        throw new Error('No data returned.');
    }

    return data.value;
}

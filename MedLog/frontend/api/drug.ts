export async function apiGetFieldDefinitions() {
    const runTimeConfig = useRuntimeConfig();
    const tokenStore = useTokenStore();

    try {
        const response = await $fetch(`${runTimeConfig.public.baseURL}v2/drug/field_def`, {
            method: 'GET',
            headers: {
                Authorization: `Bearer ${tokenStore.access_token}`,
            },
        });

        const drugFieldKeys = Object.keys(response)

        const result = drugFieldKeys.flatMap(key =>
            response[key]
                .filter(item => item.optional === false)
                .map(item => item.field_name_display)
        );

        return result;

    } catch (error) {
        console.error("Error fetching field definitions:", error);
        throw error;
    }

}

export async function apiDrugSearch(drugName: string) {
    const runTimeConfig = useRuntimeConfig();
    const tokenStore = useTokenStore();

    const result = await fetch(
        `${runTimeConfig.public.baseURL}v2/drug/search?search_term=${drugName}&only_current_medications=true&offset=0&limit=100`,
        {
            method: "GET",
            headers: { Authorization: "Bearer " + tokenStore.access_token },
        }
    );

    return result
}
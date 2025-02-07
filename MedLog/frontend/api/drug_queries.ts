export async function getFieldDefinitions() {
    const runTimeConfig = useRuntimeConfig()
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
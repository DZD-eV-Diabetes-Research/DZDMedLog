export async function apiGetFieldDefinitions(type: string) {
    const runTimeConfig = useRuntimeConfig();
    const tokenStore = useTokenStore();
    const { $api } = useNuxtApp();


    try {
        const response = await $api(`${runTimeConfig.public.baseURL}drug/field_def`);

        const filterFn = (item: any) => type === 'search_result' ? item.optional === false : true

        // Once Everything is set and fixed
        //const filterFn = (item: any) => 
        // type === 'search_result' ? item.show_in_search_result === true :
        // type === 'dynamic_form' ? item.used_for_custom_drug === true :
        // true;

        const categorizedList = {
            attrs: response.attrs?.filter(filterFn).map(item => [item.field_name_display, item.field_name, item.value_type]) || [],
            attrs_ref: response.attrs_ref?.filter(filterFn).map(item => [item.field_name_display, item.field_name, item.value_type]) || [],
            attrs_multi: response.attrs_multi?.filter(filterFn).map(item => [item.field_name_display, item.field_name, item.value_type]) || [],
            attrs_multi_ref: response.attrs_multi_ref?.filter(filterFn).map(item => [item.field_name_display, item.field_name, item.value_type]) || [],
        };

        return categorizedList;

    } catch (error) {
        console.error("Error fetching field definitions:", error);
        throw error;
    }
}

export async function apiDrugSearch(drugName: string) {
    const runTimeConfig = useRuntimeConfig();
    const tokenStore = useTokenStore();
    const { $api } = useNuxtApp();

    const result = await $api(
        `${runTimeConfig.public.baseURL}drug/search?search_term=${drugName}&only_current_medications=true&offset=0&limit=100`);

    return result
}
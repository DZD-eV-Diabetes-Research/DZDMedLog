import { useNuxtApp } from '#app';
// not needed but for IDE error messaging 
import { useRuntimeConfig } from '#imports';

export async function apiGetFieldDefinitions(type: string) {
    
    ///
    // This is function get's the information from the `drug/field_def`-endpoint
    // to use in other parts of the app
    ///

    const { $medlogapi } = useNuxtApp();


    try {
        //
        /// Utter chaos, why I chose to transform everything into an array and not an object is, not fathomable to me at this moment, mea culpa
        //
        const response = await $medlogapi("/api/drug/field_def");        
        const filterFn = (item: any) => 
        type === 'search_result' ? item.show_in_search_results === true :
        type === 'dynamic_form' ? item.used_for_custom_drug === true :
        true;

        const categorizedList = {
            attrs: response.attrs?.filter(filterFn).map((item:any)  => [item.field_name_display, item.field_name, item.value_type, item.field_desc, item.is_large_reference_list]) || [],
            attrs_ref: response.attrs_ref?.filter(filterFn).map((item:any) => [item.field_name_display, item.field_name, item.value_type, item.field_desc, item.is_large_reference_list]) || [],
            attrs_multi: response.attrs_multi?.filter(filterFn).map((item:any) => [item.field_name_display, item.field_name, item.value_type, item.field_desc, item.is_large_reference_list]) || [],
            attrs_multi_ref: response.attrs_multi_ref?.filter(filterFn).map((item:any) => [item.field_name_display, item.field_name, item.value_type, item.field_desc, item.is_large_reference_list]) || [],
        };
        
        return categorizedList;

    } catch (error) {
        console.error("Error fetching field definitions:", error);
        throw error;
    }
}

export async function apiDrugSearch(drugName: string) {
    
    ///
    // This is function uses the /drug/search endpoint to serach for the drugs
    ///

    const { $medlogapi } = useNuxtApp();

    try {
        const result = await $medlogapi(`/api/drug/search?search_term={drug}&only_current_medications=true&offset=0&limit=100`,{
            path: {
                drug: drugName
            }
        });
        return result

    } catch (error) {
        console.error("Error while searching drug:", error);
        throw error;
    }
}
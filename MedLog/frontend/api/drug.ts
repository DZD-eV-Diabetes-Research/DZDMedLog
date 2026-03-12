import { useMedlogapi } from '#imports';

export async function apiGetFieldDefinitions(type: string) {
    
    ///
    // This is function gets the information from the `drug/field_def`-endpoint
    // to use in other parts of the app
    ///

    //
    /// Utter chaos, why I chose to transform everything into an array and not an object is, not fathomable to me at this moment, mea culpa
    //
    const { data: fieldDefinitions, error } = await useMedlogapi("/api/drug/field_def");
    if (error.value) {
        throw error.value;
    }

    const filterFn = (item: any) => {
        if (type === 'search_result') {
            return item.show_in_search_results === true;
        } else if (type === 'dynamic_form') {
            return item.used_for_custom_drug === true;
        }
        return true;
    };

    return {
        attrs: fieldDefinitions.value?.attrs?.filter(filterFn).map((item: any) => [item.field_name_display, item.field_name, item.value_type, item.field_desc, item.is_large_reference_list]) || [],
        attrs_ref: fieldDefinitions.value?.attrs_ref?.filter(filterFn).map((item: any) => [item.field_name_display, item.field_name, item.value_type, item.field_desc, item.is_large_reference_list]) || [],
        attrs_multi: fieldDefinitions.value?.attrs_multi?.filter(filterFn).map((item: any) => [item.field_name_display, item.field_name, item.value_type, item.field_desc, item.is_large_reference_list]) || [],
        attrs_multi_ref: fieldDefinitions.value?.attrs_multi_ref?.filter(filterFn).map((item: any) => [item.field_name_display, item.field_name, item.value_type, item.field_desc, item.is_large_reference_list]) || [],
    };
}

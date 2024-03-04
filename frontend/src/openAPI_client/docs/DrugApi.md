# MedLogRestApi.DrugApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**getDrugDrugByPznPznGet**](DrugApi.md#getDrugDrugByPznPznGet) | **GET** /drug/by-pzn/{pzn} | Get Drug
[**listApopflichtDrugEnumApopflichtGet**](DrugApi.md#listApopflichtDrugEnumApopflichtGet) | **GET** /drug/enum/apopflicht | List Apopflicht
[**listApopflichtDrugEnumPreisartGet**](DrugApi.md#listApopflichtDrugEnumPreisartGet) | **GET** /drug/enum/preisart | List Apopflicht
[**listApplikationsformsDrugEnumAppformGet**](DrugApi.md#listApplikationsformsDrugEnumAppformGet) | **GET** /drug/enum/appform | List Applikationsforms
[**listApplikationsformsDrugEnumAppformKeyGet**](DrugApi.md#listApplikationsformsDrugEnumAppformKeyGet) | **GET** /drug/enum/appform/{key} | List Applikationsforms
[**listDarreichungsformsDrugEnumDarrformGet**](DrugApi.md#listDarreichungsformsDrugEnumDarrformGet) | **GET** /drug/enum/darrform | List Darreichungsforms
[**listDrugsDrugGet**](DrugApi.md#listDrugsDrugGet) | **GET** /drug | List Drugs
[**listGenerikakennsDrugEnumGenerikakennGet**](DrugApi.md#listGenerikakennsDrugEnumGenerikakennGet) | **GET** /drug/enum/generikakenn | List Generikakenns
[**listPackgroesseDrugEnumNormpackungsgroessenGet**](DrugApi.md#listPackgroesseDrugEnumNormpackungsgroessenGet) | **GET** /drug/enum/normpackungsgroessen | List Packgroesse
[**searchDrugsDrugSearchGet**](DrugApi.md#searchDrugsDrugSearchGet) | **GET** /drug/search | Search Drugs



## getDrugDrugByPznPznGet

> StammRead getDrugDrugByPznPznGet(pzn)

Get Drug

Get a drugs data by its PZN

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.DrugApi();
let pzn = "pzn_example"; // String | 
apiInstance.getDrugDrugByPznPznGet(pzn, (error, data, response) => {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
});
```

### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **pzn** | **String**|  | 

### Return type

[**StammRead**](StammRead.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## listApopflichtDrugEnumApopflichtGet

> PaginatedResponseApoPflicht listApopflichtDrugEnumApopflichtGet(opts)

List Apopflicht

list ApoPflicht

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.DrugApi();
let opts = {
  'offset': 0, // Number | 
  'limit': 100, // Number | 
  'orderBy': "orderBy_example", // String | 
  'orderDesc': false // Boolean | 
};
apiInstance.listApopflichtDrugEnumApopflichtGet(opts, (error, data, response) => {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
});
```

### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **offset** | **Number**|  | [optional] [default to 0]
 **limit** | **Number**|  | [optional] [default to 100]
 **orderBy** | **String**|  | [optional] 
 **orderDesc** | **Boolean**|  | [optional] [default to false]

### Return type

[**PaginatedResponseApoPflicht**](PaginatedResponseApoPflicht.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## listApopflichtDrugEnumPreisartGet

> PaginatedResponsePreisart listApopflichtDrugEnumPreisartGet(opts)

List Apopflicht

list Preisart

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.DrugApi();
let opts = {
  'offset': 0, // Number | 
  'limit': 100, // Number | 
  'orderBy': "orderBy_example", // String | 
  'orderDesc': false // Boolean | 
};
apiInstance.listApopflichtDrugEnumPreisartGet(opts, (error, data, response) => {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
});
```

### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **offset** | **Number**|  | [optional] [default to 0]
 **limit** | **Number**|  | [optional] [default to 100]
 **orderBy** | **String**|  | [optional] 
 **orderDesc** | **Boolean**|  | [optional] [default to false]

### Return type

[**PaginatedResponsePreisart**](PaginatedResponsePreisart.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## listApplikationsformsDrugEnumAppformGet

> PaginatedResponseApplikationsform listApplikationsformsDrugEnumAppformGet(opts)

List Applikationsforms

list Applikationsform

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.DrugApi();
let opts = {
  'offset': 0, // Number | 
  'limit': 100, // Number | 
  'orderBy': "orderBy_example", // String | 
  'orderDesc': false // Boolean | 
};
apiInstance.listApplikationsformsDrugEnumAppformGet(opts, (error, data, response) => {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
});
```

### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **offset** | **Number**|  | [optional] [default to 0]
 **limit** | **Number**|  | [optional] [default to 100]
 **orderBy** | **String**|  | [optional] 
 **orderDesc** | **Boolean**|  | [optional] [default to false]

### Return type

[**PaginatedResponseApplikationsform**](PaginatedResponseApplikationsform.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## listApplikationsformsDrugEnumAppformKeyGet

> Applikationsform listApplikationsformsDrugEnumAppformKeyGet(key)

List Applikationsforms

list Applikationsform

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.DrugApi();
let key = "key_example"; // String | 
apiInstance.listApplikationsformsDrugEnumAppformKeyGet(key, (error, data, response) => {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
});
```

### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **key** | **String**|  | 

### Return type

[**Applikationsform**](Applikationsform.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## listDarreichungsformsDrugEnumDarrformGet

> PaginatedResponseDarreichungsform listDarreichungsformsDrugEnumDarrformGet(opts)

List Darreichungsforms

list ...

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.DrugApi();
let opts = {
  'offset': 0, // Number | 
  'limit': 100, // Number | 
  'orderBy': "orderBy_example", // String | 
  'orderDesc': false // Boolean | 
};
apiInstance.listDarreichungsformsDrugEnumDarrformGet(opts, (error, data, response) => {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
});
```

### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **offset** | **Number**|  | [optional] [default to 0]
 **limit** | **Number**|  | [optional] [default to 100]
 **orderBy** | **String**|  | [optional] 
 **orderDesc** | **Boolean**|  | [optional] [default to false]

### Return type

[**PaginatedResponseDarreichungsform**](PaginatedResponseDarreichungsform.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## listDrugsDrugGet

> PaginatedResponseStammRead listDrugsDrugGet(opts)

List Drugs

List all medicine/drugs from the system. Needs admin role.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.DrugApi();
let opts = {
  'offset': 0, // Number | 
  'limit': 100, // Number | 
  'orderBy': "orderBy_example", // String | 
  'orderDesc': false // Boolean | 
};
apiInstance.listDrugsDrugGet(opts, (error, data, response) => {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
});
```

### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **offset** | **Number**|  | [optional] [default to 0]
 **limit** | **Number**|  | [optional] [default to 100]
 **orderBy** | **String**|  | [optional] 
 **orderDesc** | **Boolean**|  | [optional] [default to false]

### Return type

[**PaginatedResponseStammRead**](PaginatedResponseStammRead.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## listGenerikakennsDrugEnumGenerikakennGet

> PaginatedResponseGenerikakennung listGenerikakennsDrugEnumGenerikakennGet(opts)

List Generikakenns

list Generikakennung

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.DrugApi();
let opts = {
  'offset': 0, // Number | 
  'limit': 100, // Number | 
  'orderBy': "orderBy_example", // String | 
  'orderDesc': false // Boolean | 
};
apiInstance.listGenerikakennsDrugEnumGenerikakennGet(opts, (error, data, response) => {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
});
```

### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **offset** | **Number**|  | [optional] [default to 0]
 **limit** | **Number**|  | [optional] [default to 100]
 **orderBy** | **String**|  | [optional] 
 **orderDesc** | **Boolean**|  | [optional] [default to false]

### Return type

[**PaginatedResponseGenerikakennung**](PaginatedResponseGenerikakennung.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## listPackgroesseDrugEnumNormpackungsgroessenGet

> PaginatedResponseNormpackungsgroessen listPackgroesseDrugEnumNormpackungsgroessenGet(opts)

List Packgroesse

list normpackungsgroessen

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.DrugApi();
let opts = {
  'offset': 0, // Number | 
  'limit': 100, // Number | 
  'orderBy': "orderBy_example", // String | 
  'orderDesc': false // Boolean | 
};
apiInstance.listPackgroesseDrugEnumNormpackungsgroessenGet(opts, (error, data, response) => {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
});
```

### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **offset** | **Number**|  | [optional] [default to 0]
 **limit** | **Number**|  | [optional] [default to 100]
 **orderBy** | **String**|  | [optional] 
 **orderDesc** | **Boolean**|  | [optional] [default to false]

### Return type

[**PaginatedResponseNormpackungsgroessen**](PaginatedResponseNormpackungsgroessen.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## searchDrugsDrugSearchGet

> PaginatedResponseMedLogSearchEngineResult searchDrugsDrugSearchGet(searchTerm, opts)

Search Drugs

Search medicine/drugs from the system

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.DrugApi();
let searchTerm = "searchTerm_example"; // String | A search term. Can be multiple words or a single one. One word must be at least 3 chars or contained in a longer quoted string (e.g. `'Salofalk 1 g'` instead of `Salofalk 1 g`)
let opts = {
  'pznContains': "pznContains_example", // String | 
  'filterPackgroesse': "filterPackgroesse_example", // String | 
  'filterDarrform': "filterDarrform_example", // String | 
  'filterAppform': "filterAppform_example", // String | 
  'filterNormpackungsgroeeZuzahlstufe': "filterNormpackungsgroeeZuzahlstufe_example", // String | 
  'filterAtcLevel2': "filterAtcLevel2_example", // String | 
  'filterGenerikakenn': "filterGenerikakenn_example", // String | 
  'filterApopflicht': 56, // Number | 
  'filterPreisartNeu': "filterPreisartNeu_example", // String | 
  'onlyCurrentMedications': true, // Boolean | 
  'offset': 0, // Number | 
  'limit': 100, // Number | 
  'orderBy': "orderBy_example", // String | 
  'orderDesc': false // Boolean | 
};
apiInstance.searchDrugsDrugSearchGet(searchTerm, opts, (error, data, response) => {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
});
```

### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **searchTerm** | **String**| A search term. Can be multiple words or a single one. One word must be at least 3 chars or contained in a longer quoted string (e.g. &#x60;&#39;Salofalk 1 g&#39;&#x60; instead of &#x60;Salofalk 1 g&#x60;) | 
 **pznContains** | **String**|  | [optional] 
 **filterPackgroesse** | **String**|  | [optional] 
 **filterDarrform** | **String**|  | [optional] 
 **filterAppform** | **String**|  | [optional] 
 **filterNormpackungsgroeeZuzahlstufe** | **String**|  | [optional] 
 **filterAtcLevel2** | **String**|  | [optional] 
 **filterGenerikakenn** | **String**|  | [optional] 
 **filterApopflicht** | **Number**|  | [optional] 
 **filterPreisartNeu** | **String**|  | [optional] 
 **onlyCurrentMedications** | **Boolean**|  | [optional] [default to true]
 **offset** | **Number**|  | [optional] [default to 0]
 **limit** | **Number**|  | [optional] [default to 100]
 **orderBy** | **String**|  | [optional] 
 **orderDesc** | **Boolean**|  | [optional] [default to false]

### Return type

[**PaginatedResponseMedLogSearchEngineResult**](PaginatedResponseMedLogSearchEngineResult.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


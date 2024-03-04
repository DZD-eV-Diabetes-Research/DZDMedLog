# MedLogRestApi.StudyApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**createStudyStudyPost**](StudyApi.md#createStudyStudyPost) | **POST** /study | Create Study
[**deleteStudyStudyStudyIdDelete**](StudyApi.md#deleteStudyStudyStudyIdDelete) | **DELETE** /study/{study_id} | Delete Study
[**listStudiesStudyGet**](StudyApi.md#listStudiesStudyGet) | **GET** /study | List Studies
[**updateStudyStudyStudyIdPatch**](StudyApi.md#updateStudyStudyStudyIdPatch) | **PATCH** /study/{study_id} | Update Study



## createStudyStudyPost

> Study createStudyStudyPost(studyCreate)

Create Study

Create a new study. Needs admin role.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.StudyApi();
let studyCreate = new MedLogRestApi.StudyCreate(); // StudyCreate | 
apiInstance.createStudyStudyPost(studyCreate, (error, data, response) => {
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
 **studyCreate** | [**StudyCreate**](StudyCreate.md)|  | 

### Return type

[**Study**](Study.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json


## deleteStudyStudyStudyIdDelete

> deleteStudyStudyStudyIdDelete(studyId)

Delete Study

Delete existing study - Not Yet Implented

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.StudyApi();
let studyId = "studyId_example"; // String | 
apiInstance.deleteStudyStudyStudyIdDelete(studyId, (error, data, response) => {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully.');
  }
});
```

### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **studyId** | **String**|  | 

### Return type

null (empty response body)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## listStudiesStudyGet

> PaginatedResponseStudy listStudiesStudyGet(opts)

List Studies

List all studies the user has access too.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.StudyApi();
let opts = {
  'showDeactived': false, // Boolean | 
  'offset': 0, // Number | 
  'limit': 100, // Number | 
  'orderBy': "orderBy_example", // String | 
  'orderDesc': false // Boolean | 
};
apiInstance.listStudiesStudyGet(opts, (error, data, response) => {
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
 **showDeactived** | **Boolean**|  | [optional] [default to false]
 **offset** | **Number**|  | [optional] [default to 0]
 **limit** | **Number**|  | [optional] [default to 100]
 **orderBy** | **String**|  | [optional] 
 **orderDesc** | **Boolean**|  | [optional] [default to false]

### Return type

[**PaginatedResponseStudy**](PaginatedResponseStudy.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## updateStudyStudyStudyIdPatch

> Study updateStudyStudyStudyIdPatch(studyId, studyUpdate)

Update Study

Update existing study

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.StudyApi();
let studyId = "studyId_example"; // String | 
let studyUpdate = new MedLogRestApi.StudyUpdate(); // StudyUpdate | 
apiInstance.updateStudyStudyStudyIdPatch(studyId, studyUpdate, (error, data, response) => {
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
 **studyId** | **String**|  | 
 **studyUpdate** | [**StudyUpdate**](StudyUpdate.md)|  | 

### Return type

[**Study**](Study.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json


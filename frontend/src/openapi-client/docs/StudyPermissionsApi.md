# MedLogRestApi.StudyPermissionsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**createOrUpdatePermissionStudyStudyIdPermissionsUserIdPut**](StudyPermissionsApi.md#createOrUpdatePermissionStudyStudyIdPermissionsUserIdPut) | **PUT** /study/{study_id}/permissions/{user_id} | Create Or Update Permission
[**getPermissionDetailsStudyStudyIdPermissionsPermissionIdGet**](StudyPermissionsApi.md#getPermissionDetailsStudyStudyIdPermissionsPermissionIdGet) | **GET** /study/{study_id}/permissions/{permission_id} | Get Permission Details
[**listStudyPermissionsStudyStudyIdPermissionsGet**](StudyPermissionsApi.md#listStudyPermissionsStudyStudyIdPermissionsGet) | **GET** /study/{study_id}/permissions | List Study Permissions



## createOrUpdatePermissionStudyStudyIdPermissionsUserIdPut

> StudyPermissonUpdate createOrUpdatePermissionStudyStudyIdPermissionsUserIdPut(userId, studyId, studyPermissonUpdate)

Create Or Update Permission

Create or update new study permision for a user.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.StudyPermissionsApi();
let userId = "userId_example"; // String | 
let studyId = new MedLogRestApi.StudyId(); // StudyId | 
let studyPermissonUpdate = new MedLogRestApi.StudyPermissonUpdate(); // StudyPermissonUpdate | 
apiInstance.createOrUpdatePermissionStudyStudyIdPermissionsUserIdPut(userId, studyId, studyPermissonUpdate, (error, data, response) => {
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
 **userId** | **String**|  | 
 **studyId** | [**StudyId**](.md)|  | 
 **studyPermissonUpdate** | [**StudyPermissonUpdate**](StudyPermissonUpdate.md)|  | 

### Return type

[**StudyPermissonUpdate**](StudyPermissonUpdate.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json


## getPermissionDetailsStudyStudyIdPermissionsPermissionIdGet

> StudyPermisson getPermissionDetailsStudyStudyIdPermissionsPermissionIdGet(permissionId, studyId)

Get Permission Details

List all medicine intakes of one probands last completed interview.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.StudyPermissionsApi();
let permissionId = "permissionId_example"; // String | 
let studyId = new MedLogRestApi.StudyId(); // StudyId | 
apiInstance.getPermissionDetailsStudyStudyIdPermissionsPermissionIdGet(permissionId, studyId, (error, data, response) => {
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
 **permissionId** | **String**|  | 
 **studyId** | [**StudyId**](.md)|  | 

### Return type

[**StudyPermisson**](StudyPermisson.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## listStudyPermissionsStudyStudyIdPermissionsGet

> PaginatedResponseStudyPermissionRead listStudyPermissionsStudyStudyIdPermissionsGet(studyId, opts)

List Study Permissions

List all access permissons for a study. User must be system admin, system user manager or study admin to see these.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.StudyPermissionsApi();
let studyId = new MedLogRestApi.StudyId(); // StudyId | 
let opts = {
  'offset': 0, // Number | 
  'limit': 100, // Number | 
  'orderBy': "orderBy_example", // String | 
  'orderDesc': false // Boolean | 
};
apiInstance.listStudyPermissionsStudyStudyIdPermissionsGet(studyId, opts, (error, data, response) => {
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
 **studyId** | [**StudyId**](.md)|  | 
 **offset** | **Number**|  | [optional] [default to 0]
 **limit** | **Number**|  | [optional] [default to 100]
 **orderBy** | **String**|  | [optional] 
 **orderDesc** | **Boolean**|  | [optional] [default to false]

### Return type

[**PaginatedResponseStudyPermissionRead**](PaginatedResponseStudyPermissionRead.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


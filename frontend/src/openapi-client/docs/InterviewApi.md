# MedLogRestApi.InterviewApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**createInterviewStudyStudyIdEventEventIdInterviewPost**](InterviewApi.md#createInterviewStudyStudyIdEventEventIdInterviewPost) | **POST** /study/{study_id}/event/{event_id}/interview | Create Interview
[**deleteInterviewStudyStudyIdEventEventIdInterviewInterviewIdDelete**](InterviewApi.md#deleteInterviewStudyStudyIdEventEventIdInterviewInterviewIdDelete) | **DELETE** /study/{study_id}/event/{event_id}/interview/{interview_id} | Delete Interview
[**getInterviewStudyStudyIdEventEventIdInterviewInterviewIdGet**](InterviewApi.md#getInterviewStudyStudyIdEventEventIdInterviewInterviewIdGet) | **GET** /study/{study_id}/event/{event_id}/interview/{interview_id} | Get Interview
[**getLastCompletedInterviewStudyStudyIdProbandProbandIdInterviewLastGet**](InterviewApi.md#getLastCompletedInterviewStudyStudyIdProbandProbandIdInterviewLastGet) | **GET** /study/{study_id}/proband/{proband_id}/interview/last | Get Last Completed Interview
[**getLastNonCompletedInterviewStudyStudyIdProbandProbandIdInterviewCurrentGet**](InterviewApi.md#getLastNonCompletedInterviewStudyStudyIdProbandProbandIdInterviewCurrentGet) | **GET** /study/{study_id}/proband/{proband_id}/interview/current | Get Last Non Completed Interview
[**listAllInterviewsOfStudyStudyStudyIdInterviewGet**](InterviewApi.md#listAllInterviewsOfStudyStudyStudyIdInterviewGet) | **GET** /study/{study_id}/interview | List All Interviews Of Study
[**listInterviewsByStudyEventStudyStudyIdEventEventIdInterviewGet**](InterviewApi.md#listInterviewsByStudyEventStudyStudyIdEventEventIdInterviewGet) | **GET** /study/{study_id}/event/{event_id}/interview | List Interviews By Study Event
[**listInterviewsOfProbandStudyStudyIdProbandProbandIdInterviewGet**](InterviewApi.md#listInterviewsOfProbandStudyStudyIdProbandProbandIdInterviewGet) | **GET** /study/{study_id}/proband/{proband_id}/interview | List Interviews Of Proband
[**updateInterviewStudyStudyIdEventEventIdInterviewInterviewIdPatch**](InterviewApi.md#updateInterviewStudyStudyIdEventEventIdInterviewInterviewIdPatch) | **PATCH** /study/{study_id}/event/{event_id}/interview/{interview_id} | Update Interview



## createInterviewStudyStudyIdEventEventIdInterviewPost

> [Interview] createInterviewStudyStudyIdEventEventIdInterviewPost(eventId, studyId, interviewCreate)

Create Interview

Create new interview

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.InterviewApi();
let eventId = "eventId_example"; // String | 
let studyId = new MedLogRestApi.StudyId(); // StudyId | 
let interviewCreate = new MedLogRestApi.InterviewCreate(); // InterviewCreate | 
apiInstance.createInterviewStudyStudyIdEventEventIdInterviewPost(eventId, studyId, interviewCreate, (error, data, response) => {
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
 **eventId** | **String**|  | 
 **studyId** | [**StudyId**](.md)|  | 
 **interviewCreate** | [**InterviewCreate**](InterviewCreate.md)|  | 

### Return type

[**[Interview]**](Interview.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json


## deleteInterviewStudyStudyIdEventEventIdInterviewInterviewIdDelete

> deleteInterviewStudyStudyIdEventEventIdInterviewInterviewIdDelete(interviewId, eventId, studyId)

Delete Interview

Delete existing interview - Not Yet Implented

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.InterviewApi();
let interviewId = "interviewId_example"; // String | 
let eventId = "eventId_example"; // String | 
let studyId = new MedLogRestApi.StudyId(); // StudyId | 
apiInstance.deleteInterviewStudyStudyIdEventEventIdInterviewInterviewIdDelete(interviewId, eventId, studyId, (error, data, response) => {
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
 **interviewId** | **String**|  | 
 **eventId** | **String**|  | 
 **studyId** | [**StudyId**](.md)|  | 

### Return type

null (empty response body)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## getInterviewStudyStudyIdEventEventIdInterviewInterviewIdGet

> Interview getInterviewStudyStudyIdEventEventIdInterviewInterviewIdGet(eventId, interviewId, studyId)

Get Interview

Get a certain interview by its id.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.InterviewApi();
let eventId = "eventId_example"; // String | 
let interviewId = "interviewId_example"; // String | 
let studyId = new MedLogRestApi.StudyId(); // StudyId | 
apiInstance.getInterviewStudyStudyIdEventEventIdInterviewInterviewIdGet(eventId, interviewId, studyId, (error, data, response) => {
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
 **eventId** | **String**|  | 
 **interviewId** | **String**|  | 
 **studyId** | [**StudyId**](.md)|  | 

### Return type

[**Interview**](Interview.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## getLastCompletedInterviewStudyStudyIdProbandProbandIdInterviewLastGet

> Interview getLastCompletedInterviewStudyStudyIdProbandProbandIdInterviewLastGet(probandId, studyId)

Get Last Completed Interview

Get the last completed interview of proband.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.InterviewApi();
let probandId = "probandId_example"; // String | 
let studyId = new MedLogRestApi.StudyId(); // StudyId | 
apiInstance.getLastCompletedInterviewStudyStudyIdProbandProbandIdInterviewLastGet(probandId, studyId, (error, data, response) => {
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
 **probandId** | **String**|  | 
 **studyId** | [**StudyId**](.md)|  | 

### Return type

[**Interview**](Interview.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## getLastNonCompletedInterviewStudyStudyIdProbandProbandIdInterviewCurrentGet

> Interview getLastNonCompletedInterviewStudyStudyIdProbandProbandIdInterviewCurrentGet(probandId, studyId)

Get Last Non Completed Interview

Get the latest non completed interview of proband.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.InterviewApi();
let probandId = "probandId_example"; // String | 
let studyId = new MedLogRestApi.StudyId(); // StudyId | 
apiInstance.getLastNonCompletedInterviewStudyStudyIdProbandProbandIdInterviewCurrentGet(probandId, studyId, (error, data, response) => {
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
 **probandId** | **String**|  | 
 **studyId** | [**StudyId**](.md)|  | 

### Return type

[**Interview**](Interview.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## listAllInterviewsOfStudyStudyStudyIdInterviewGet

> [Interview] listAllInterviewsOfStudyStudyStudyIdInterviewGet(studyId)

List All Interviews Of Study

List all interviews of one study.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.InterviewApi();
let studyId = new MedLogRestApi.StudyId(); // StudyId | 
apiInstance.listAllInterviewsOfStudyStudyStudyIdInterviewGet(studyId, (error, data, response) => {
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

### Return type

[**[Interview]**](Interview.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## listInterviewsByStudyEventStudyStudyIdEventEventIdInterviewGet

> [Interview] listInterviewsByStudyEventStudyStudyIdEventEventIdInterviewGet(eventId, studyId)

List Interviews By Study Event

List all interviews of an event.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.InterviewApi();
let eventId = "eventId_example"; // String | 
let studyId = new MedLogRestApi.StudyId(); // StudyId | 
apiInstance.listInterviewsByStudyEventStudyStudyIdEventEventIdInterviewGet(eventId, studyId, (error, data, response) => {
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
 **eventId** | **String**|  | 
 **studyId** | [**StudyId**](.md)|  | 

### Return type

[**[Interview]**](Interview.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## listInterviewsOfProbandStudyStudyIdProbandProbandIdInterviewGet

> [Interview] listInterviewsOfProbandStudyStudyIdProbandProbandIdInterviewGet(probandId, studyId)

List Interviews Of Proband

List all interviews of one proband.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.InterviewApi();
let probandId = "probandId_example"; // String | 
let studyId = new MedLogRestApi.StudyId(); // StudyId | 
apiInstance.listInterviewsOfProbandStudyStudyIdProbandProbandIdInterviewGet(probandId, studyId, (error, data, response) => {
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
 **probandId** | **String**|  | 
 **studyId** | [**StudyId**](.md)|  | 

### Return type

[**[Interview]**](Interview.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## updateInterviewStudyStudyIdEventEventIdInterviewInterviewIdPatch

> Interview updateInterviewStudyStudyIdEventEventIdInterviewInterviewIdPatch(interviewId, eventId, studyId, interviewUpdate)

Update Interview

Update existing interview

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.InterviewApi();
let interviewId = "interviewId_example"; // String | 
let eventId = "eventId_example"; // String | 
let studyId = new MedLogRestApi.StudyId(); // StudyId | 
let interviewUpdate = new MedLogRestApi.InterviewUpdate(); // InterviewUpdate | 
apiInstance.updateInterviewStudyStudyIdEventEventIdInterviewInterviewIdPatch(interviewId, eventId, studyId, interviewUpdate, (error, data, response) => {
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
 **interviewId** | **String**|  | 
 **eventId** | **String**|  | 
 **studyId** | [**StudyId**](.md)|  | 
 **interviewUpdate** | [**InterviewUpdate**](InterviewUpdate.md)|  | 

### Return type

[**Interview**](Interview.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json


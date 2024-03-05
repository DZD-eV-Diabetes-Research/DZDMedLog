# MedLogRestApi.EventApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**createEventStudyStudyIdEventPost**](EventApi.md#createEventStudyStudyIdEventPost) | **POST** /study/{study_id}/event | Create Event
[**deleteEventStudyStudyIdEventEventIdDelete**](EventApi.md#deleteEventStudyStudyIdEventEventIdDelete) | **DELETE** /study/{study_id}/event/{event_id} | Delete Event
[**listEventsStudyStudyIdEventGet**](EventApi.md#listEventsStudyStudyIdEventGet) | **GET** /study/{study_id}/event | List Events
[**updateEventStudyStudyIdEventEventIdPatch**](EventApi.md#updateEventStudyStudyIdEventEventIdPatch) | **PATCH** /study/{study_id}/event/{event_id} | Update Event



## createEventStudyStudyIdEventPost

> Event createEventStudyStudyIdEventPost(studyId, event)

Create Event

Create a new event.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.EventApi();
let studyId = new MedLogRestApi.StudyId(); // StudyId | 
let event = new MedLogRestApi.Event(); // Event | 
apiInstance.createEventStudyStudyIdEventPost(studyId, event, (error, data, response) => {
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
 **event** | [**Event**](Event.md)|  | 

### Return type

[**Event**](Event.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json


## deleteEventStudyStudyIdEventEventIdDelete

> deleteEventStudyStudyIdEventEventIdDelete(eventId, studyId)

Delete Event

Delete existing event - Not Yet Implented

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.EventApi();
let eventId = "eventId_example"; // String | 
let studyId = new MedLogRestApi.StudyId(); // StudyId | 
apiInstance.deleteEventStudyStudyIdEventEventIdDelete(eventId, studyId, (error, data, response) => {
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
 **eventId** | **String**|  | 
 **studyId** | [**StudyId**](.md)|  | 

### Return type

null (empty response body)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## listEventsStudyStudyIdEventGet

> PaginatedResponseEvent listEventsStudyStudyIdEventGet(studyId, opts)

List Events

List all studies the user has access too.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.EventApi();
let studyId = new MedLogRestApi.StudyId(); // StudyId | 
let opts = {
  'hideCompleted': false, // Boolean | 
  'offset': 0, // Number | 
  'limit': 100, // Number | 
  'orderBy': "orderBy_example", // String | 
  'orderDesc': false // Boolean | 
};
apiInstance.listEventsStudyStudyIdEventGet(studyId, opts, (error, data, response) => {
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
 **hideCompleted** | **Boolean**|  | [optional] [default to false]
 **offset** | **Number**|  | [optional] [default to 0]
 **limit** | **Number**|  | [optional] [default to 100]
 **orderBy** | **String**|  | [optional] 
 **orderDesc** | **Boolean**|  | [optional] [default to false]

### Return type

[**PaginatedResponseEvent**](PaginatedResponseEvent.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## updateEventStudyStudyIdEventEventIdPatch

> Event updateEventStudyStudyIdEventEventIdPatch(eventId, studyId, eventUpdate)

Update Event

Update existing event

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.EventApi();
let eventId = "eventId_example"; // String | 
let studyId = new MedLogRestApi.StudyId(); // StudyId | 
let eventUpdate = new MedLogRestApi.EventUpdate(); // EventUpdate | 
apiInstance.updateEventStudyStudyIdEventEventIdPatch(eventId, studyId, eventUpdate, (error, data, response) => {
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
 **eventUpdate** | [**EventUpdate**](EventUpdate.md)|  | 

### Return type

[**Event**](Event.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json


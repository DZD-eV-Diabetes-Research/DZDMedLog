# MedLogRestApi.IntakeApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**createIntakeStudyStudyIdInterviewInterviewIdIntakePost**](IntakeApi.md#createIntakeStudyStudyIdInterviewInterviewIdIntakePost) | **POST** /study/{study_id}/interview/{interview_id}/intake | Create Intake
[**deleteIntakeStudyStudyIdInterviewInterviewIdIntakeIntakeIdDelete**](IntakeApi.md#deleteIntakeStudyStudyIdInterviewInterviewIdIntakeIntakeIdDelete) | **DELETE** /study/{study_id}/interview/{interview_id}/intake/{intake_id} | Delete Intake
[**getIntakeStudyStudyIdInterviewInterviewIdIntakeIntakeIdGet**](IntakeApi.md#getIntakeStudyStudyIdInterviewInterviewIdIntakeIntakeIdGet) | **GET** /study/{study_id}/interview/{interview_id}/intake/{intake_id} | Get Intake
[**listAllIntakesOfInterviewStudyStudyIdInterviewInterviewIdIntakeGet**](IntakeApi.md#listAllIntakesOfInterviewStudyStudyIdInterviewInterviewIdIntakeGet) | **GET** /study/{study_id}/interview/{interview_id}/intake | List All Intakes Of Interview
[**listAllIntakesOfLastCompletedInterviewStudyStudyIdProbandProbandIdInterviewLastIntakeGet**](IntakeApi.md#listAllIntakesOfLastCompletedInterviewStudyStudyIdProbandProbandIdInterviewLastIntakeGet) | **GET** /study/{study_id}/proband/{proband_id}/interview/last/intake | List All Intakes Of Last Completed Interview
[**listAllIntakesOfLastUncompletedInterviewStudyStudyIdProbandProbandIdInterviewCurrentIntakeGet**](IntakeApi.md#listAllIntakesOfLastUncompletedInterviewStudyStudyIdProbandProbandIdInterviewCurrentIntakeGet) | **GET** /study/{study_id}/proband/{proband_id}/interview/current/intake | List All Intakes Of Last Uncompleted Interview
[**updateIntakeStudyStudyIdInterviewInterviewIdIntakeIntakeIdPatch**](IntakeApi.md#updateIntakeStudyStudyIdInterviewInterviewIdIntakeIntakeIdPatch) | **PATCH** /study/{study_id}/interview/{interview_id}/intake/{intake_id} | Update Intake



## createIntakeStudyStudyIdInterviewInterviewIdIntakePost

> [Intake] createIntakeStudyStudyIdInterviewInterviewIdIntakePost(interviewId, studyId, intakeCreate)

Create Intake

Create intake record in certain interview. user must have at least &#39;interviewer&#39;-permissions on study.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.IntakeApi();
let interviewId = "interviewId_example"; // String | 
let studyId = new MedLogRestApi.StudyId(); // StudyId | 
let intakeCreate = new MedLogRestApi.IntakeCreate(); // IntakeCreate | 
apiInstance.createIntakeStudyStudyIdInterviewInterviewIdIntakePost(interviewId, studyId, intakeCreate, (error, data, response) => {
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
 **studyId** | [**StudyId**](.md)|  | 
 **intakeCreate** | [**IntakeCreate**](IntakeCreate.md)|  | 

### Return type

[**[Intake]**](Intake.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json


## deleteIntakeStudyStudyIdInterviewInterviewIdIntakeIntakeIdDelete

> [Intake] deleteIntakeStudyStudyIdInterviewInterviewIdIntakeIntakeIdDelete(interviewId, intakeId, studyId)

Delete Intake

Update intake record. user must have at least &#39;interviewer&#39;-permissions on study.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.IntakeApi();
let interviewId = "interviewId_example"; // String | 
let intakeId = "intakeId_example"; // String | 
let studyId = new MedLogRestApi.StudyId(); // StudyId | 
apiInstance.deleteIntakeStudyStudyIdInterviewInterviewIdIntakeIntakeIdDelete(interviewId, intakeId, studyId, (error, data, response) => {
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
 **intakeId** | **String**|  | 
 **studyId** | [**StudyId**](.md)|  | 

### Return type

[**[Intake]**](Intake.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## getIntakeStudyStudyIdInterviewInterviewIdIntakeIntakeIdGet

> Intake getIntakeStudyStudyIdInterviewInterviewIdIntakeIntakeIdGet(interviewId, intakeId, studyId)

Get Intake

Get a certain intake record by it id

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.IntakeApi();
let interviewId = "interviewId_example"; // String | 
let intakeId = "intakeId_example"; // String | 
let studyId = new MedLogRestApi.StudyId(); // StudyId | 
apiInstance.getIntakeStudyStudyIdInterviewInterviewIdIntakeIntakeIdGet(interviewId, intakeId, studyId, (error, data, response) => {
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
 **intakeId** | **String**|  | 
 **studyId** | [**StudyId**](.md)|  | 

### Return type

[**Intake**](Intake.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## listAllIntakesOfInterviewStudyStudyIdInterviewInterviewIdIntakeGet

> [Intake] listAllIntakesOfInterviewStudyStudyIdInterviewInterviewIdIntakeGet(interviewId, studyId)

List All Intakes Of Interview

List all medicine intakes of interview.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.IntakeApi();
let interviewId = "interviewId_example"; // String | 
let studyId = new MedLogRestApi.StudyId(); // StudyId | 
apiInstance.listAllIntakesOfInterviewStudyStudyIdInterviewInterviewIdIntakeGet(interviewId, studyId, (error, data, response) => {
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
 **studyId** | [**StudyId**](.md)|  | 

### Return type

[**[Intake]**](Intake.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## listAllIntakesOfLastCompletedInterviewStudyStudyIdProbandProbandIdInterviewLastIntakeGet

> [Intake] listAllIntakesOfLastCompletedInterviewStudyStudyIdProbandProbandIdInterviewLastIntakeGet(probandId, studyId)

List All Intakes Of Last Completed Interview

List all medicine intakes of one probands last completed interview.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.IntakeApi();
let probandId = "probandId_example"; // String | 
let studyId = new MedLogRestApi.StudyId(); // StudyId | 
apiInstance.listAllIntakesOfLastCompletedInterviewStudyStudyIdProbandProbandIdInterviewLastIntakeGet(probandId, studyId, (error, data, response) => {
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

[**[Intake]**](Intake.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## listAllIntakesOfLastUncompletedInterviewStudyStudyIdProbandProbandIdInterviewCurrentIntakeGet

> [Intake] listAllIntakesOfLastUncompletedInterviewStudyStudyIdProbandProbandIdInterviewCurrentIntakeGet(probandId, studyId)

List All Intakes Of Last Uncompleted Interview

List all medicine intakes of one probands last completed interview.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.IntakeApi();
let probandId = "probandId_example"; // String | 
let studyId = new MedLogRestApi.StudyId(); // StudyId | 
apiInstance.listAllIntakesOfLastUncompletedInterviewStudyStudyIdProbandProbandIdInterviewCurrentIntakeGet(probandId, studyId, (error, data, response) => {
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

[**[Intake]**](Intake.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## updateIntakeStudyStudyIdInterviewInterviewIdIntakeIntakeIdPatch

> [Intake] updateIntakeStudyStudyIdInterviewInterviewIdIntakeIntakeIdPatch(interviewId, intakeId, studyId, intakeUpdate)

Update Intake

Update intake record. user must have at least &#39;interviewer&#39;-permissions on study.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.IntakeApi();
let interviewId = "interviewId_example"; // String | 
let intakeId = "intakeId_example"; // String | 
let studyId = new MedLogRestApi.StudyId(); // StudyId | 
let intakeUpdate = new MedLogRestApi.IntakeUpdate(); // IntakeUpdate | 
apiInstance.updateIntakeStudyStudyIdInterviewInterviewIdIntakeIntakeIdPatch(interviewId, intakeId, studyId, intakeUpdate, (error, data, response) => {
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
 **intakeId** | **String**|  | 
 **studyId** | [**StudyId**](.md)|  | 
 **intakeUpdate** | [**IntakeUpdate**](IntakeUpdate.md)|  | 

### Return type

[**[Intake]**](Intake.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json


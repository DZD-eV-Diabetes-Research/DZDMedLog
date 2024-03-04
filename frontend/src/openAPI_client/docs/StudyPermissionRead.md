# MedLogRestApi.StudyPermissionRead

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**isStudyViewer** | **Boolean** | This is the minimal access to a study. The user can see all data but can not alter anything | [optional] [default to true]
**isStudyInterviewer** | **Boolean** | Study interviewers can create new interview entries for this study. | [optional] [default to false]
**isStudyAdmin** | **Boolean** | Study admins can give access to the study to new users. | [optional] [default to false]
**studyId** | **String** |  | 
**userId** | **String** |  | 
**id** | **String** |  | 
**userRef** | [**User**](User.md) |  | 
**studyRef** | [**Study**](Study.md) |  | 



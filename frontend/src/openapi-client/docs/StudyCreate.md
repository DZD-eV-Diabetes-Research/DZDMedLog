# MedLogRestApi.StudyCreate

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**displayName** | [**DisplayName**](DisplayName.md) |  | [optional] 
**deactivated** | **Boolean** |  | [optional] [default to false]
**noPermissions** | **Boolean** | If this is set to True all user have access as interviewers to the study. This can be utile when this MedLog instance only host one study.  Admin access still need to be allocated explicit. | [optional] [default to false]
**id** | [**Id**](Id.md) |  | 
**name** | **String** | The identifiying name of the study. This can not be changed later. Must be a &#39;[Slug](https://en.wikipedia.org/wiki/Clean_URL#Slug)&#39;; A human and machine reable string containing no spaces, only numbers, lowered latin-script-letters and dashes. If you need to change the name later, use the display name. | 



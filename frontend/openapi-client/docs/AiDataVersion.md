# MedLogRestApi.AiDataVersion

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**createdAt** | **Date** |  | [optional] 
**id** | **String** |  | [optional] 
**dateiversion** | **String** | Dateiversion | 
**datenstand** | **String** | Monat Datenstand (JJJJMM) | 
**importCompletedAt** | [**ImportCompletedAt**](ImportCompletedAt.md) |  | [optional] 
**deactivated** | **Boolean** | If set to true this arzneimittel index version will be ignored (when not queried for explciet in the crud interface). This can be helpfull e.g. if the last import contained dirty data and one wants to fallback on the previous version. | [optional] [default to false]



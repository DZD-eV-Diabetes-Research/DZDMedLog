# MedLogRestApi.IntakeCreate

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | [**Id**](Id.md) |  | 
**interviewId** | [**InterviewId**](InterviewId.md) |  | 
**pharmazentralnummer** | **String** | Take the Pharmazentralnummer in many formats, but all formats will be normalized to just a 8 digit number. | 
**intakeStartTimeUtc** | **Date** |  | 
**intakeEndTimeUtc** | [**IntakeEndTimeUtc**](IntakeEndTimeUtc.md) |  | [optional] 
**administeredByDoctor** | [**IntakeAdministeredByDoctor**](IntakeAdministeredByDoctor.md) |  | [optional] 
**intakeRegularOrAsNeeded** | [**IntakeIntakeRegularOrAsNeeded**](IntakeIntakeRegularOrAsNeeded.md) |  | [optional] 
**dosePerDay** | [**DosePerDay**](DosePerDay.md) |  | [optional] 
**regularIntervallOfDailyDose** | [**IntakeRegularIntervallOfDailyDose**](IntakeRegularIntervallOfDailyDose.md) |  | [optional] 
**asNeededDoseUnit** | [**AsNeededDoseUnit**](AsNeededDoseUnit.md) |  | 
**consumedMedsToday** | [**ConsumedMedsTodayAnswers**](ConsumedMedsTodayAnswers.md) |  | 



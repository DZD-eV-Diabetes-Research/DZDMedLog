# MedLogRestApi.StammRead

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**createdAt** | **Date** |  | [optional] 
**aiVersionId** | **String** | Foreing key to &#39;AiDataVersion&#39; (&#39;GKV WiDo Arzneimittel Index&#39; Data Format Version) which contains the information which Arzneimittel Index &#39;Datenstand&#39; and &#39;Dateiversion&#39; the row has | 
**laufnr** | **String** | Laufende Nummer (vom WIdO vergeben) | 
**stakenn** | [**Stakenn**](Stakenn.md) |  | 
**staname** | **String** | Standardaggregatname (vom WIdO vergeben) (enhält *NV* wenn &#39;Noch nicht abschließend klassifiziertes Arzneimittel&#39;) | 
**atcCode** | [**AtcCode**](AtcCode.md) |  | 
**indgr** | **String** | Indikationsgruppe (nach Roter Liste 2014) | 
**pzn** | **String** | Pharmazentralnummer | 
**name** | **String** | Präparatename | 
**herstellerCode** | **String** | Herstellerschlüssel (Siehe &#x60;hersteller_ref&#x60; für vollen Herstellernamen) | 
**darrform** | **String** | Darreichungsformschlüssel (Siehe &#x60;darrform_ref&#x60; für vollen Namen) | 
**zuzahlstufe** | [**Zuzahlstufe**](Zuzahlstufe.md) |  | 
**packgroesse** | **Number** | Packungsgröße (in 1/10 Einheiten) | 
**dddpk** | **String** | DDD je Packung (nach WIdO, in 1/1000 Einheiten) | 
**apopflicht** | **Number** | Apotheken-/Rezeptpflichtschlüssel (Siehe &#x60;apopflicht_ref&#x60; für vollen Namen) | 
**preisartAlt** | [**PreisartAlt**](PreisartAlt.md) |  | 
**preisartNeu** | [**PreisartNeu**](PreisartNeu.md) |  | 
**preisAlt** | **Number** | Preis alt (in Cent) | 
**preisNeu** | **Number** | Preis neu (in Cent) | 
**festbetrag** | **Number** | Festbetrag (in Cent) | 
**marktzugang** | [**Marktzugang**](Marktzugang.md) |  | 
**ahdatum** | [**Ahdatum**](Ahdatum.md) |  | 
**rueckruf** | **Boolean** | Rückruf/zurückgezogen oder zurückgezogen durch Hersteller | 
**generikakenn** | **Number** | Generika-Kennung | 
**appform** | [**Appform**](Appform.md) |  | 
**biosimilar** | [**Biosimilar1**](Biosimilar1.md) |  | 
**orphan** | **Boolean** | Von der EMA mit Orphan Drug Status zugelassene Arzneimittel (Klassifikation zum Stichtag) | 
**aiVersionRef** | [**AiDataVersion**](AiDataVersion.md) |  | 
**darrformRef** | [**Darreichungsform**](Darreichungsform.md) |  | 
**appformRef** | [**StammReadAppformRef**](StammReadAppformRef.md) |  | 
**zuzahlstufeRef** | [**StammReadZuzahlstufeRef**](StammReadZuzahlstufeRef.md) |  | 
**herstellerRef** | [**Hersteller**](Hersteller.md) |  | 
**apopflichtRef** | [**ApoPflicht**](ApoPflicht.md) |  | 
**preisartNeuRef** | [**StammReadPreisartNeuRef**](StammReadPreisartNeuRef.md) |  | 
**preisartAltRef** | [**StammReadPreisartNeuRef**](StammReadPreisartNeuRef.md) |  | 
**biosimilarRef** | [**StammReadBiosimilarRef**](StammReadBiosimilarRef.md) |  | 
**generikakennRef** | [**Generikakennung**](Generikakennung.md) |  | 



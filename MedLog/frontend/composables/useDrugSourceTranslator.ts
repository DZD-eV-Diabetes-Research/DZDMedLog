// Translation helper, since the backend is in English but the interface is in German

export default function (eng:string|null = null, de:string|null = null) {
  let english = [
    "Study participant: verbal specification",
    "Medication package: Scanned PZN",
    "Medication package: Typed in PZN",
    "Medication package: Drug name",
    "Medication leaflet",
    "Study participant: medication plan",
    "Study participant: Medication prescription",
    "Follow up via phone/message: Typed in PZN",
    "Follow up via phone/message: Medication name",
  ];

  let deutsch = [
    "Probandenangabe",
    "Medikamentenpackung: PZN gescannt",
    "Medikamentenpackung: PZN getippt",
    "Medikamentenpackung: Arzneimittelname",
    "Beipackzettel",
    "Medikamentenplan",
    "Rezept",
    "Nacherhebung: Tastatureingabe der PZN",
    "Nacherhebung: Arzneimittelname"
  ]

  if (eng === null && de === null) {
    return ""
  }

  if (eng !== null){    
    const index = english.indexOf(eng)
    return deutsch[index]
  } else if (de !== null){
    const index = deutsch.indexOf(de)
    return english[index]
  } else {
    return "Please enter something"
  }
}
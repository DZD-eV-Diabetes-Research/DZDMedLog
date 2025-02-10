export default function (eng:string|null = null, de:string|null = null) {
    
    let english = [
      "Unknown",
      "Daily",
      "every 2. day",
      "every 3. day",
      "every 4. day / twice a week",
      "intervals of one week or more"
    ];
  
    let deutsch = [
      "unbekannt",
      "täglich",
      "jeden 2. Tag",
      "jeden 3. Tag",
      "jeden 4. Tag = 2x pro Woche",
      "Im Abstand von 1 Woche und mehr"
    ]

    if (eng === null && de === null) {
        return null;
      }
  
    if (eng !== null){
      const index = english.indexOf(eng)
      return deutsch[index]
    } else if (de !== null){
      const index = deutsch.indexOf(de)
      return english[index]
    } 
  }
  
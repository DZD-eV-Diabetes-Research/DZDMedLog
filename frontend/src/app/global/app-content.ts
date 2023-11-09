export class AppContent {
    //Common
    static readonly Title: string = "IDOM";
    static readonly SearchByKeyWord: string = "Nach Bezeichnung suchen";
    static readonly FirstName: string = 'Vorname';
    static readonly LastName: string = 'Nachname';
    static readonly Email: string = 'Email';
    static readonly Status: string = 'Status';
    static readonly Action: string = 'Aktion';
    static readonly Logout: string = 'Abmelden';
    static readonly Name: string = 'Name';
    static readonly Save: string = 'Speichern';
    static readonly ConductInterview: string = 'Interview durchführen';
    static readonly SearchMedicine: string = 'Medikamente suchen';
    static readonly ExportInterviews: string = 'Interviews exportieren';
    static readonly Configuration: string = 'Konfiguration';
    static readonly DataManagement: string = 'Datenverwaltung';
    static readonly NoFileSelected: string = 'Es wurde noch keine Datei hinzugefügt!'
    static readonly IsRequired: string = ' ist erforderlich';

    //User Management
    static readonly UserTitle: string = 'Benutzerübersicht';
    static readonly SelectRole: string = 'Rolle auswählen';
    static readonly SelectStatus: string = 'Status auswählen';
    static readonly UserManagement: string = 'Benutzerverwaltung';
    static readonly Admin: string = 'Administrator';
    static readonly Deactivated: string = 'Deaktiviert';
    static readonly UserDetails: string = 'Benutzerdetails';
    static readonly DeleteRequestMessage: string = 'Sind Sie sicher, dass Sie den/die ausgewählten Benutzer löschen möchten?';
    static readonly DeleteRequestHeader: string = 'Benutzer löschen';
    static readonly DeleteRequestApproval: string = 'Benutzer gelöscht';
    static readonly CreateRequestApproval: string = 'Benutzer erstellt';
    static readonly EditRequestApproval: string = 'Benutzer aktualisiert';
    static readonly FileRequestApproval: string = 'Datei hochgeladen';


    //Drug Management
    static readonly DrugEmptyPlaceHolder: string = 'Es wurde noch keine Droge hinzugefügt!';
    static readonly DrugName: string = ' Arzneimittel-Bezeichnung';
    static readonly ManufacturerKey: string = 'Hersteller-Schlüssel';
    static readonly DosageForm: string = 'Darreichungs-form';
    static readonly ApplicationForm: string = 'Applikations-form';
    static readonly ATC: string = 'ATC';
    static readonly PZN: string = 'PZN';
    static readonly PackingSize: string = 'Packungs-größe';
    static readonly StandardPackageSize: string = 'Norm-packungs-größe';
    static readonly FromTrade: string = 'Aus dem Handel/der MedDB';
    static readonly DrugSearchEmptyPlaceHolder: string = 'Keine Medikamente gefunden.';
    static readonly NewDrug: string = "Neues Medikament";
    static readonly PharmaCentralNumber: string = "Pharmazentralnummer";
    static readonly DosageFormInput: string = "Darreichungsform";
    static readonly ApplicationFormInput: string = "Applikationsform";
    static readonly PackageSize: string = 'Packungsgröße';
    static readonly StandardPackageSizeInput :string = 'Normpackungsgröße';
    static readonly ManufacturerKeyInput :string = 'Herstellerschlüssel';
    static readonly PriceInCent :string = 'Preis in Cent';
    static readonly FixedPriceInCent :string = 'Festpreis in Cent';

    // Event Management
    static readonly EventManagement: string = 'Event-IDs';
    static readonly EventName: string = 'Name';
    static readonly EventDescription: string = 'Beschreibung';
    static readonly EventEmptyPlaceholder: string = 'Keine Events gefunden.'

    //Interview
    static readonly ProbandStep: string = 'Proband';
    static readonly DrugStep: string = 'Medikamente';
    static readonly ConfirmationStep: string = 'Bestätigung';
    static readonly NextPage: string = 'Weiter';
    static readonly PreviousPage: string = 'Zurück';
    
    static readonly ProbandInformationTitle: string = 'Probanden Informationen';
    static readonly ProbandInformationSubtitle: string = 'Bitte füllen Sie die folgenden Felder aus.';
    static readonly ProbandId: string = 'Probanden-ID';
    static readonly EventId: string = 'Event-ID';
    static readonly InterviewerNumber: string = 'Interviewer-Nummer';
    static readonly StartTime: string = 'Startzeitpunkt';
    static readonly DrugIntakeNotice: string = 'Haben Sie Diabetes-Medikamente in den vergangenen 12 Monaten bzw. andere Medikamente in den letzten 7 Tagen eingenommen?';

    static readonly DrugSelectionTitle: string = 'Erfasste Medikamente';
    static readonly DrugSelectionSubtitle: string = 'Diese Medikamente wurden bisher erfasst.'
    static readonly NoDrugsDocumented: string = 'Keine Medikamente erfasst.';

    static readonly IntakeInformationTitle: string = 'Zusätzliche Informationen';
    static readonly IntakeInformationSubtitle: string = 'Bitte füllen Sie die folgenden Felder aus.';
    static readonly ForDiabetesDrugs: string = 'Bei Diabetes-Medikamenten:';
    static readonly Intake: string = 'Einnahme:';
    static readonly StartDate: string = 'Startdatum';
    static readonly EndDate: string = 'Enddatum';
    static readonly AdditionalInformation: string = 'Zusatzinformationen';
    static readonly IsPrescribed: string = 'Vom Arzt verordnet?';
    static readonly IsRegularly: string = 'Ist die Einnahme regelmäßig?';
    static readonly DosePerDay: string = 'Dosis pro Tag';
    static readonly IntakeInterval: string = 'Intervall der Tagesdosen';
    static readonly DoseUnit: string = 'Einheit der Dosis';
    static readonly TakenToday: string = 'Medikament heute eingenommen?';
    static readonly Notice: string = 'Bemerkungen';
    static readonly SourceOfDrugData: string = 'Quelle der Arzneimittelangaben';

    static readonly ConfirmInterviewTitle: string = 'Bestätigung der Eingaben';
    static readonly InterestSpecificDrugs: string = 'Ganz bestimmte Medikamentengruppen sind für uns von besonderem Interesse.';
    static readonly InsulinDocumented: string = 'Haben sie Insulinpräparate angegeben, falls Sie diese einnehmen?';
    static readonly OnlyWomen: string = 'Nur bei Frauen:';
    static readonly HormoneDrugDocumented: string = 'Haben Sie die Pille bzw. Hormonersatzpräparate (einschließlich Depotpräparate und Pflaster) angegeben, falls Sie diese einehmen?';
    static readonly EndTime: string = 'Endzeitpunkt';
}
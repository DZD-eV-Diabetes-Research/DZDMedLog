import { Intake } from "./intake";

export class IntakeDTO {
    drugId?: number;
    startDate?: Date;
    endDate?: Date;
    prescribed: boolean = false;
    regularly: boolean = false;
    dosePerDay?: number;
    intakeInterval?: string;
    doseUnit?: string;
    takenToday: boolean = false;
    note?: string;
    sourceOfDrugData?: string;

    public static fromIntake(intake: Intake): IntakeDTO {
        var dto: any = Object.assign({}, intake);
        delete dto.drug;
        dto.drugId = intake.drug?.pharmaceuticalCentralNumber;
        return dto as IntakeDTO;
    }
}
import { Drug } from "../drug/drug";

export class Intake {
    drug?: Drug;
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
}
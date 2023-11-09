import { IntakeDTO } from "./intake-dto";

export class Interview {
    probandId: string;
    eventId: number;
    interviewerNumber: number;
    startDate: Date;
    endDate: Date;
    hasTakenOtherDrugs: boolean;
    intakes: IntakeDTO[] = [] as IntakeDTO[];
}
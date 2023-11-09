import { Component } from '@angular/core';
import { DynamicDialogConfig, DynamicDialogRef } from "primeng/dynamicdialog";
import { AppContent } from '../global/app-content';
import { Intake } from '../shared/interview/intake';
import { InterviewService } from '../shared/interview/interview.service';

@Component({
  selector: 'app-intake-information',
  templateUrl: './intake-information.component.html',
  styleUrls: ['./intake-information.component.scss']
})
export class IntakeInformationComponent {

  readonly AppContent = AppContent;

  intake: Intake = {} as Intake;
  submitted: boolean = false;

  intakeIntervals: String[];
  doseUnits: String[];
  sourcesOfDrugData: String[];

  constructor(private ref: DynamicDialogRef, private dialogConfig: DynamicDialogConfig, private interviewService: InterviewService) {
    this.intakeIntervals = ["DAILY", "WEEKLY", "MONTHLY"];
    this.doseUnits = ["mg", "l", "?"];
    this.sourcesOfDrugData = ["Proband", "Interviewer"];
    this.intake.drug = dialogConfig.data.drug;
  }

  addIntake() {
    if (this.intake.startDate
      && this.intake.endDate
      && this.intake.sourceOfDrugData
      && (!this.intake.regularly ||
        (this.intake.dosePerDay
          && this.intake.intakeInterval
          && this.intake.doseUnit))) {
      this.ref.close(this.intake)
      return;
    }
    this.submitted = true;
  }

}

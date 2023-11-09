import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AppContent } from '../global/app-content';
import { InterviewService } from '../shared/interview/interview.service';

@Component({
  selector: 'app-proband-information',
  templateUrl: './proband-information.component.html',
  styleUrls: ['./proband-information.component.scss']
})
export class ProbandInformationComponent {

  readonly AppContent = AppContent;

  submitted: boolean = false;

  constructor(public router: Router, public interviewService: InterviewService) {}

  ngOnInit() {
    if (!this.interviewService.startDate) {
      this.interviewService.startDate = new Date();
    }
  }

  nextPage() {
    if (this.interviewService.probandId 
        && this.interviewService.eventId 
        && this.interviewService.interviewerNumber 
        && this.interviewService.startDate) {
      this.router.navigate(['interview/drug']);
    }
    this.submitted = true;
  }
}

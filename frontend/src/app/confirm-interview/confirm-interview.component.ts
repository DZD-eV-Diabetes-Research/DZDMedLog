import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AppContent } from '../global/app-content';
import { InterviewService } from '../shared/interview/interview.service';

@Component({
  selector: 'app-confirm-interview',
  templateUrl: './confirm-interview.component.html',
  styleUrls: ['./confirm-interview.component.scss']
})
export class ConfirmInterviewComponent {

  readonly AppContent = AppContent;

  submitted: boolean = false;

  constructor(private router: Router, public interviewService: InterviewService) { }

  ngOnInit() {
    if (!this.interviewService.endDate) {
      this.interviewService.endDate = new Date();
    }
  }

  previousPage() {
    this.router.navigate(['/interview/drug']);
  }

  save() {
    if (this.interviewService.endDate) {
      this.interviewService.saveInterview().subscribe(() => {
        this.interviewService.clearService();
        this.router.navigate(['/welcome']);
      });
      return;
    }
    this.submitted = true;
  }
}

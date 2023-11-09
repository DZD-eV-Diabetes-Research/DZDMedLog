import { Component } from '@angular/core';
import { MenuItem, MessageService } from 'primeng/api';
import { AppContent } from '../global/app-content';

@Component({
  selector: 'app-perform-interview',
  templateUrl: './perform-interview.component.html',
  styleUrls: ['./perform-interview.component.scss']
})
export class PerformInterviewComponent {

  readonly AppContent = AppContent;

  items: MenuItem[];

  constructor(public messageService: MessageService) { }

  ngOnInit() {
    this.items = [{
      label: AppContent.ProbandStep,
      routerLink: 'proband'
    },
    {
      label: AppContent.DrugStep,
      routerLink: 'drug'
    },
    {
      label: AppContent.ConfirmationStep,
      routerLink: 'confirm'
    }
    ];
  }
}

import { Component, OnInit } from '@angular/core';
import { AppContent } from '../global/app-content';
import { Event } from '../shared/event/event';
import { EventService } from '../shared/event/event.service';
import { DynamicDialogRef } from 'primeng/dynamicdialog';

@Component({
  selector: 'app-create-event',
  templateUrl: './create-event.component.html',
  styleUrls: ['./create-event.component.scss']
})
export class CreateEventComponent implements OnInit {
  readonly AppContent = AppContent;

  eventDetails: Event;

  constructor(private eventService: EventService, private ref: DynamicDialogRef) { }

  ngOnInit(): void {
    this.eventDetails = new Event();
  }

  addEvent(): void {
    if (!this.eventDetails.id)
      this.eventService.addEvent(this.eventDetails).subscribe(() => this.ref.close(true));
  }

}

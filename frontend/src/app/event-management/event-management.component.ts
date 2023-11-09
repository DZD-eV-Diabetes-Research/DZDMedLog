import { Component, OnInit } from '@angular/core';
import { AppContent } from '../global/app-content';
import { Event } from '../shared/event/event';
import { EventService } from '../shared/event/event.service';
import { DialogService } from 'primeng/dynamicdialog';
import { CreateDrugComponent } from '../create-drug/create-drug.component';
import { CreateEventComponent } from '../create-event/create-event.component';

@Component({
  selector: 'app-event-management',
  templateUrl: './event-management.component.html',
  styleUrls: ['./event-management.component.scss']
})
export class EventManagementComponent implements OnInit {
  readonly AppContent = AppContent;

  events: Event[] = [];

  constructor (private eventService: EventService, private dialogeService: DialogService) { }

  ngOnInit(): void {
    this.loadEvents();
  }
  
  loadEvents(): void {
    this.eventService.getAllEvents().subscribe(events => this.events = events);
  }

  showCreateEventDialog() {
    this.dialogeService.open(CreateEventComponent, {header: "Neues Event", width: "500px"}).onClose.subscribe(eventCreated => {
      this.loadEvents();
    });
  }
}

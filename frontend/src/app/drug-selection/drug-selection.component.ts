import { Component, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { DialogService } from "primeng/dynamicdialog";
import { Table } from 'primeng/table';
import { CreateDrugComponent } from '../create-drug/create-drug.component';
import { AppContent } from '../global/app-content';
import { IntakeInformationComponent } from '../intake-information/intake-information.component';
import { Drug, DrugPageRequest, DrugPageResponse } from '../shared/drug/drug';
import { DrugService } from '../shared/drug/drug.service';
import { Intake } from '../shared/interview/intake';
import { InterviewService } from '../shared/interview/interview.service';
import { LazyLoadEvent } from 'primeng/api';

@Component({
  selector: 'app-drug-selection',
  templateUrl: './drug-selection.component.html',
  styleUrls: ['./drug-selection.component.scss']
})
export class DrugSelectionComponent {

  readonly AppContent = AppContent;

  drugs: Drug[] = [];
  totalRecords: number = 0;
  totalPages: number = 0;

  intakes: Intake[] = [];

  @ViewChild('drugDataTable') drugDataTable: Table | undefined;
  @ViewChild('intakeDataTable') intakeDataTable: Table | undefined;

  constructor(public router: Router, public drugService: DrugService, public interviewService: InterviewService, public dialogService: DialogService) {}

  loadDrugs($event: LazyLoadEvent) {
    let multiSortMeta = $event.multiSortMeta === null ? undefined : $event.multiSortMeta,
        sortField: string | undefined = undefined,
        sortOrder: number | undefined = undefined;

    if (multiSortMeta !== undefined && multiSortMeta.length === 1) {
        sortField = multiSortMeta.at(0)?.field;
        sortOrder = multiSortMeta.at(0)?.order;
        multiSortMeta = undefined;
    }

    const drugPageRequest: DrugPageRequest = {
      size: $event.rows,
      page: ($event.first === undefined || $event.rows === undefined) ? undefined : $event.first / $event.rows,
      globalFilter: $event.globalFilter === null ? undefined : $event.globalFilter,
      multiSortMeta: multiSortMeta,
      sortField: sortField,
      sortOrder: sortOrder
    }
    return this.drugService.getDrugs(drugPageRequest).subscribe((response: DrugPageResponse) => {
      this.drugs = response.content;
      this.totalRecords = response.totalElements;
      this.totalPages = response.totalPages;
    });
  }

  applyFilterGlobalDrug($event: any, stringVal: any) {
    this.drugDataTable!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
  }

  reset(table: Table | undefined) {
    const requestEvent = {
      page: 0,
      rows: this.drugDataTable === undefined ? 50 : this.drugDataTable.rows
    } as LazyLoadEvent
    table!.clear();
    this.loadDrugs(requestEvent);
  }

  addIntakeForDrug(drug: Drug) {
    this.dialogService.open(IntakeInformationComponent, {header: AppContent.IntakeInformationTitle, width: "80%", data: {drug: drug}}).onClose.subscribe((intake: Intake) => {
      if (intake) {
        this.intakes = [...this.intakes, intake];
      }
    });
  }

  deleteIntake(intake: Intake) {
    this.intakes.forEach((value, index) => {
      if (value == intake) {
        this.intakes.splice(index, 1);
        this.intakes = [...this.intakes];
      }
    });
  }

  nextPage() {
    this.interviewService.intakes = this.intakes;
    this.router.navigate(['interview/confirm']);
  }

  previousPage() {
    this.interviewService.intakes = this.intakes;
    this.router.navigate(['interview/proband']);
  }

  showCreateDrugDialog() {
    this.dialogService.open(CreateDrugComponent, {header:"Neues Medikament", width:"500px"}).onClose.subscribe(isDrugCreated => {
      this.loadDrugs({} as LazyLoadEvent);
    });
  }
}

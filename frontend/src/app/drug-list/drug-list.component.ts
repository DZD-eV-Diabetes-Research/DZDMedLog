import { Component, OnInit, ViewChild } from '@angular/core';
import { Table } from 'primeng/table';
import { Drug, DrugPageRequest, DrugPageResponse } from '../shared/drug/drug';
import { DrugService } from '../shared/drug/drug.service';
import {DialogService} from "primeng/dynamicdialog";
import {CreateDrugComponent} from "../create-drug/create-drug.component";
import { AppContent } from '../global/app-content';
import { LazyLoadEvent } from 'primeng/api';


@Component({
  selector: 'drug-list',
  templateUrl: './drug-list.component.html',
  styleUrls: ['./drug-list.component.scss'],
})
export class DrugListComponent {

  readonly AppContent = AppContent;

  drugs: Drug[] = [];
  totalRecords: number = 0;
  totalPages: number = 0;

  @ViewChild('drugDataTable') drugDataTable: Table | undefined;

  constructor(public drugService: DrugService, public dialogService: DialogService) {
  }

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

  clear(table: Table | undefined) {
    if (table !== undefined)
      table.clear();
  }
  
  reset(table: Table | undefined) {
    const requestEvent = {
      page: 0,
      rows: this.drugDataTable === undefined ? 50 : this.drugDataTable.rows
    } as LazyLoadEvent
    this.clear(table);
    this.loadDrugs(requestEvent);
  }

  applyFilterGlobal($event: any, stringVal: any) {
    this.drugDataTable!.filterGlobal(($event.target as HTMLInputElement).value, stringVal);
  }

  showCreateDrugDialog() {
    this.dialogService.open(CreateDrugComponent, {header: AppContent.NewDrug, width:"500px"}).onClose.subscribe(isDrugCreated => {
    });
  }
}
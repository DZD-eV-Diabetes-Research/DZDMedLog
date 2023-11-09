import { Component, ViewChild } from '@angular/core';
import { MessageService } from 'primeng/api';
import { AppContent } from '../global/app-content';
import {environment} from "../../environments/environment";
import { throwError } from 'rxjs';
import { FileUpload, FileUploadModule } from 'primeng/fileupload';

@Component({
  selector: 'app-data-management',
  templateUrl: './data-management.component.html',
  styleUrls: ['./data-management.component.scss']
})
export class DataManagementComponent {
  readonly AppContent = AppContent;
  environment = environment;

  
  uploadedFiles: any[] = [];

  constructor(
    private messageService: MessageService) {
}

  onUpload(event: { files: any; }) {
      for(let file of event.files) {
          this.uploadedFiles.push(file);
      }

      this.messageService.add({severity: 'success', summary: AppContent.FileRequestApproval, life: 3000});
  }

  @ViewChild('fileUpload', {static: false}) fileUpload: any;
  onError(event: {error: ErrorEvent, files: File[];}) {
    let errorMessage = event.error.message;
    this.fileUpload.clear();
    window.alert(errorMessage);
  }
}
